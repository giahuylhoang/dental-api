"""
Sync Google Calendar with Database (Database is ground truth).

This script ensures that:
1. Calendar events exist for all SCHEDULED appointments in database
2. Calendar events are deleted for appointments not in database (or cancelled/rescheduled)
3. Calendar events match database appointments (time, patient, doctor, service)

Database is the source of truth - calendar is synced to match database.
"""

import sys
import os
from datetime import datetime
import pytz

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.connection import get_db, init_db
from database.models import Patient, Appointment, Doctor, Service, AppointmentStatus
from sqlalchemy.orm import Session
from tools.calendar_tools import get_calendar_service, CalendarTokenError
from tools.doctor_calendars import get_calendar_id_for_doctor
from tools.event_template import format_calendar_event
from googleapiclient.errors import HttpError

EDMONTON_TZ = pytz.timezone('America/Edmonton')


def sync_db_to_calendar():
    """Sync calendar to match database (database is ground truth)."""
    init_db()
    
    # Get database session
    db: Session = next(get_db())
    
    try:
        # Connect to calendar
        try:
            calendar_service = get_calendar_service()
            print("✓ Connected to Google Calendar")
        except CalendarTokenError as e:
            print(f"✗ Calendar service unavailable: {e}")
            print("  Cannot sync without calendar access.")
            return
        except Exception as e:
            print(f"✗ Error connecting to calendar: {e}")
            return
        
        # 1. Get all active appointments from database
        active_statuses = [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.PENDING_SYNC,
            AppointmentStatus.PENDING
        ]
        
        db_appointments = db.query(Appointment).filter(
            Appointment.status.in_(active_statuses)
        ).all()
        
        print(f"\nFound {len(db_appointments)} active appointment(s) in database")
        
        # Track what we need to sync
        events_to_create = []
        events_to_update = []
        events_to_delete = []
        events_synced = []
        
        # 2. For each appointment in database, ensure calendar event exists and matches
        for appointment in db_appointments:
            doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
            patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
            service = db.query(Service).filter(Service.id == appointment.service_id).first() if appointment.service_id else None
            
            if not doctor:
                print(f"⚠ Appointment {appointment.id} has invalid doctor_id {appointment.doctor_id}, skipping")
                continue
            
            if not patient:
                print(f"⚠ Appointment {appointment.id} has invalid patient_id {appointment.patient_id}, skipping")
                continue
            
            calendar_id = get_calendar_id_for_doctor(doctor.name)
            
            # Prepare event data
            patient_name = f"{patient.first_name} {patient.last_name or ''}".strip()
            service_name = service.name if service else "Appointment"
            
            event_data = format_calendar_event(
                appointment_id=appointment.id,
                patient_name=patient_name,
                service_name=service_name,
                patient_id=appointment.patient_id,
                doctor_id=appointment.doctor_id,
                service_id=appointment.service_id or 0,
                reason=appointment.reason_note or ""
            )
            
            # Convert times to Edmonton timezone
            if appointment.start_time.tzinfo is None:
                start_dt_edmonton = EDMONTON_TZ.localize(appointment.start_time)
            else:
                start_dt_edmonton = appointment.start_time.astimezone(EDMONTON_TZ)
            
            if appointment.end_time.tzinfo is None:
                end_dt_edmonton = EDMONTON_TZ.localize(appointment.end_time)
            else:
                end_dt_edmonton = appointment.end_time.astimezone(EDMONTON_TZ)
            
            calendar_event = {
                "summary": event_data["summary"],
                "description": event_data["description"],
                "start": {
                    "dateTime": start_dt_edmonton.isoformat(),
                    "timeZone": str(EDMONTON_TZ),
                },
                "end": {
                    "dateTime": end_dt_edmonton.isoformat(),
                    "timeZone": str(EDMONTON_TZ),
                },
            }
            
            # Check if calendar event exists
            if appointment.calendar_event_id:
                try:
                    existing_event = calendar_service.events().get(
                        calendarId=calendar_id,
                        eventId=appointment.calendar_event_id
                    ).execute()
                    
                    # Check if event needs update (compare times)
                    existing_start = datetime.fromisoformat(
                        existing_event['start']['dateTime'].replace('Z', '+00:00')
                    )
                    existing_end = datetime.fromisoformat(
                        existing_event['end']['dateTime'].replace('Z', '+00:00')
                    )
                    
                    needs_update = (
                        existing_start != start_dt_edmonton or
                        existing_end != end_dt_edmonton or
                        existing_event.get('summary') != calendar_event['summary']
                    )
                    
                    if needs_update:
                        # Update event
                        updated_event = calendar_service.events().update(
                            calendarId=calendar_id,
                            eventId=appointment.calendar_event_id,
                            body=calendar_event
                        ).execute()
                        events_to_update.append(appointment.id)
                        print(f"  ✓ Updated calendar event for appointment {appointment.id}")
                    else:
                        events_synced.append(appointment.id)
                        print(f"  ✓ Calendar event already synced for appointment {appointment.id}")
                        
                except HttpError as e:
                    if e.resp.status == 404:
                        # Event doesn't exist, need to create it
                        events_to_create.append((appointment, calendar_id, calendar_event))
                        print(f"  ⚠ Calendar event missing for appointment {appointment.id}, will create")
                    else:
                        print(f"  ✗ Error checking calendar event {appointment.calendar_event_id}: {e}")
            else:
                # No calendar_event_id, need to create event
                events_to_create.append((appointment, calendar_id, calendar_event))
                print(f"  ⚠ No calendar event ID for appointment {appointment.id}, will create")
        
        # 3. Create missing calendar events
        print(f"\nCreating {len(events_to_create)} missing calendar event(s)...")
        for appointment, calendar_id, calendar_event in events_to_create:
            try:
                created_event = calendar_service.events().insert(
                    calendarId=calendar_id,
                    body=calendar_event
                ).execute()
                
                # Update appointment with calendar_event_id
                appointment.calendar_event_id = created_event.get('id')
                appointment.status = AppointmentStatus.SCHEDULED
                db.commit()
                
                print(f"  ✓ Created calendar event {created_event.get('id')} for appointment {appointment.id}")
            except Exception as e:
                print(f"  ✗ Failed to create calendar event for appointment {appointment.id}: {e}")
        
        # 4. Find and delete orphaned calendar events (events in calendar but not in database)
        print(f"\nChecking for orphaned calendar events...")
        
        # Get all doctors
        doctors = db.query(Doctor).filter(Doctor.is_active == True).all()
        orphaned_count = 0
        
        for doctor in doctors:
            calendar_id = get_calendar_id_for_doctor(doctor.name)
            
            try:
                # Get all events from calendar (limited to next 365 days)
                now = datetime.now(EDMONTON_TZ)
                time_min = now.isoformat()
                time_max = (now.replace(year=now.year + 1)).isoformat()
                
                events_result = calendar_service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=2500,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                calendar_events = events_result.get('items', [])
                
                # Check each calendar event
                for event in calendar_events:
                    event_id = event.get('id')
                    
                    # Skip cancelled events
                    if event.get('status') == 'cancelled':
                        continue
                    
                    # Check if this event corresponds to an appointment in database
                    appointment = db.query(Appointment).filter(
                        Appointment.calendar_event_id == event_id
                    ).first()
                    
                    if not appointment:
                        # Orphaned event - delete it
                        try:
                            calendar_service.events().delete(
                                calendarId=calendar_id,
                                eventId=event_id
                            ).execute()
                            orphaned_count += 1
                            print(f"  ✓ Deleted orphaned calendar event {event_id} (not in database)")
                        except Exception as e:
                            print(f"  ✗ Failed to delete orphaned event {event_id}: {e}")
                            
            except HttpError as e:
                print(f"  ✗ Error checking calendar {calendar_id} for doctor {doctor.name}: {e}")
            except Exception as e:
                print(f"  ✗ Error processing calendar for doctor {doctor.name}: {e}")
        
        # 5. Summary
        print(f"\n" + "=" * 60)
        print(f"Sync Summary:")
        print(f"  Database appointments: {len(db_appointments)}")
        print(f"  Events already synced: {len(events_synced)}")
        print(f"  Events created: {len(events_to_create)}")
        print(f"  Events updated: {len(events_to_update)}")
        print(f"  Orphaned events deleted: {orphaned_count}")
        print(f"\n✓ Calendar sync completed!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error syncing calendar: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Syncing Google Calendar with Database (DB is ground truth)...")
    print("=" * 60)
    sync_db_to_calendar()
