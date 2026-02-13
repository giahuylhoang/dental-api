#!/usr/bin/env python3
"""
Test Google Service Account JSON credentials.

This script verifies that GOOGLE_SERVICE_ACCOUNT_JSON is configured correctly
and can access Google Calendar API.

Usage:
    python test_google_service_account.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent
env_files = [
    project_root / ".env.local",
    project_root / ".env",
    Path.cwd() / ".env.local",
    Path.cwd() / ".env",
]

for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        break

def check_service_account_json():
    """Check if GOOGLE_SERVICE_ACCOUNT_JSON is set and valid."""
    print("🔍 Checking GOOGLE_SERVICE_ACCOUNT_JSON configuration...\n")
    
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    if not service_account_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not found!")
        print("\nSet it with:")
        print("  export GOOGLE_SERVICE_ACCOUNT_JSON='{\"type\":\"service_account\",...}'")
        print("\nOr add to .env.local:")
        print('  GOOGLE_SERVICE_ACCOUNT_JSON="{\"type\":\"service_account\",...}"')
        return None
    
    # Validate JSON format
    try:
        sa_info = json.loads(service_account_json)
        print("✅ GOOGLE_SERVICE_ACCOUNT_JSON found")
        print("✅ Valid JSON format")
        
        # Check required fields
        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if field not in sa_info]
        
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return None
        
        print(f"✅ All required fields present")
        print(f"\n📋 Service Account Info:")
        print(f"   Type: {sa_info.get('type')}")
        print(f"   Project ID: {sa_info.get('project_id')}")
        print(f"   Client Email: {sa_info.get('client_email')}")
        
        return sa_info
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        print("\nMake sure the JSON is properly formatted and escaped.")
        return None
    except Exception as e:
        print(f"❌ Error parsing JSON: {e}")
        return None

def check_dependencies():
    """Check if required Google API dependencies are installed."""
    print("\n🔍 Checking dependencies...\n")
    
    missing = []
    
    try:
        import google.auth
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        print("✅ google-auth installed")
        print("✅ google-api-python-client installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall with:")
        print("  pip install google-auth google-api-python-client")
        print("  # or")
        print("  pip install -r requirements.txt")
        return False

def test_service_account_credentials(sa_info):
    """Test service account credentials."""
    print("\n🔍 Testing service account credentials...\n")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Scopes needed for Calendar API
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        # Create credentials from service account info
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=SCOPES
        )
        print("✅ Service account credentials created successfully")
        
        # Build Calendar API service
        service = build('calendar', 'v3', credentials=creds)
        print("✅ Google Calendar API service created")
        
        return service, creds
        
    except Exception as e:
        print(f"❌ Error creating credentials: {e}")
        print("\nPossible issues:")
        print("  1. Invalid service account JSON")
        print("  2. Missing or incorrect private key")
        print("  3. Service account email format incorrect")
        return None, None

def test_calendar_access(service):
    """Test accessing Google Calendar."""
    print("\n🔍 Testing Google Calendar access...\n")
    
    try:
        # Try to list calendars
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        print(f"✅ Successfully accessed Google Calendar API")
        print(f"✅ Found {len(calendars)} calendar(s)")
        
        if calendars:
            print("\n📅 Available calendars:")
            for cal in calendars[:5]:  # Show first 5
                cal_id = cal.get('id', 'N/A')
                cal_summary = cal.get('summary', 'N/A')
                cal_access = cal.get('accessRole', 'N/A')
                print(f"   - {cal_summary} ({cal_id[:30]}...)")
                print(f"     Access: {cal_access}")
        
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Error accessing calendar: {e}")
        
        if "insufficient authentication scopes" in error_str.lower():
            print("\n⚠️  Issue: Insufficient authentication scopes")
            print("   Make sure the service account has Calendar API access")
        elif "not found" in error_str.lower() or "forbidden" in error_str.lower():
            print("\n⚠️  Issue: Calendar access denied")
            print("   You need to share your Google Calendar with the service account email")
            print(f"   Service account email: {os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') and json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')).get('client_email', 'N/A')}")
            print("\n   Steps to fix:")
            print("   1. Open Google Calendar")
            print("   2. Go to Settings → Settings for my calendars")
            print("   3. Select your calendar")
            print("   4. Share with the service account email")
            print("   5. Give it 'Make changes to events' permission")
        elif "invalid_grant" in error_str.lower():
            print("\n⚠️  Issue: Invalid credentials")
            print("   The service account JSON might be expired or invalid")
            print("   Generate a new key from Google Cloud Console")
        else:
            print("\n⚠️  Check:")
            print("  1. Google Calendar API is enabled in Google Cloud Console")
            print("  2. Service account has proper permissions")
            print("  3. Calendar is shared with service account email")
        
        return False

def test_create_event(service):
    """Test creating a test event (optional)."""
    print("\n🔍 Testing event creation (optional test)...\n")
    
    try:
        from datetime import datetime, timedelta
        
        # Get primary calendar
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            print("⚠️  No calendars found to test event creation")
            return False
        
        primary_calendar = calendars[0]['id']
        
        # Create a test event 1 hour from now
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        event = {
            'summary': 'Test Event - Can be deleted',
            'description': 'This is a test event created by the service account test script',
            'start': {
                'dateTime': start_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
        }
        
        created_event = service.events().insert(
            calendarId=primary_calendar,
            body=event
        ).execute()
        
        event_id = created_event.get('id')
        print(f"✅ Test event created successfully!")
        print(f"   Event ID: {event_id}")
        print(f"   Summary: {created_event.get('summary')}")
        print(f"   Start: {created_event['start'].get('dateTime')}")
        
        # Optionally delete the test event
        print("\n🗑️  Cleaning up test event...")
        try:
            service.events().delete(
                calendarId=primary_calendar,
                eventId=event_id
            ).execute()
            print("✅ Test event deleted")
        except:
            print("⚠️  Could not delete test event (you can delete it manually)")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Event creation test failed: {e}")
        print("   This is optional - calendar access is more important")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Google Service Account Test")
    print("=" * 60)
    print()
    
    # Step 1: Check configuration
    sa_info = check_service_account_json()
    if not sa_info:
        print("\n❌ Configuration check failed.")
        return 1
    
    # Step 2: Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n❌ Dependencies check failed.")
        return 1
    
    # Step 3: Test credentials
    service, creds = test_service_account_credentials(sa_info)
    if not service:
        print("\n❌ Credentials test failed.")
        return 1
    
    # Step 4: Test calendar access
    access_ok = test_calendar_access(service)
    
    # Step 5: Test event creation (optional)
    create_ok = test_create_event(service)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Configuration:  {'✅ PASS' if sa_info else '❌ FAIL'}")
    print(f"  Dependencies:   {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"  Credentials:    {'✅ PASS' if service else '❌ FAIL'}")
    print(f"  Calendar Access: {'✅ PASS' if access_ok else '❌ FAIL'}")
    print(f"  Event Creation: {'✅ PASS' if create_ok else '⚠️  SKIP'}")
    print("=" * 60)
    
    if sa_info and deps_ok and service and access_ok:
        print("\n✅ All critical tests passed! Your Google Service Account is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Your service account can access Google Calendar")
        print("   2. Make sure calendars are shared with the service account email")
        print("   3. Your application is ready to use Google Calendar API")
        return 0
    elif sa_info and deps_ok and service:
        print("\n⚠️  Credentials work, but calendar access failed.")
        print("   Make sure to share your calendar with the service account email.")
        return 1
    else:
        print("\n❌ Some tests failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
