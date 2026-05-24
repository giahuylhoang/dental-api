"""
Seed demo clinic data for the 'default' clinic.

Idempotent: exits 0 with "already seeded" if >5 invoices already exist.
"""
import sys
import os
import random
from datetime import datetime, timedelta

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def main():
    from faker import Faker
    from sqlalchemy.orm import Session, sessionmaker

    import database.models  # noqa: register models
    import database.clinical.models  # noqa
    import database.ops.models  # noqa

    from database.connection import engine, Base
    from database.models import (
        Clinic, Patient, Provider, Lead, LeadStatus, DEFAULT_CLINIC_ID,
    )
    from database.clinical.models import (
        LabVendor, LabCase, TreatmentPlan, TreatmentPlanItem, DentureCase,
    )
    from database.ops.models import Invoice, InvoiceLine, Communication
    from clients.lab_case_numbering import next_lab_case_number

    # Skip tables that require PG-only types (Vector, JSONB, TEXT[]) when running on SQLite
    _SQLITE_SKIP = {"rag_docs", "clinic_routing"}
    if engine.dialect.name == "sqlite":
        _tables = [t for t in Base.metadata.sorted_tables if t.name not in _SQLITE_SKIP]
        Base.metadata.create_all(bind=engine, tables=_tables)
    else:
        Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()

    try:
        # Idempotency check
        inv_count = db.query(Invoice).filter(Invoice.clinic_id == DEFAULT_CLINIC_ID).count()
        if inv_count > 5:
            print("already seeded")
            return

        fake = Faker()
        random.seed(42)
        Faker.seed(42)

        # Ensure default clinic exists
        clinic = db.query(Clinic).filter(Clinic.id == DEFAULT_CLINIC_ID).first()
        if not clinic:
            clinic = Clinic(
                id=DEFAULT_CLINIC_ID,
                name="Demo Dental Clinic",
                display_name="Demo Dental Clinic",
                timezone="America/Edmonton",
                working_hour_start=9,
                working_hour_end=17,
            )
            db.add(clinic)
            db.flush()

        # ── Providers ──────────────────────────────────────────────────────
        provider_specs = [
            ("Dr. Alice Nguyen", "Dr", "General Dentistry"),
            ("Dr. Bob Patel", "Dr", "Prosthodontics"),
            ("Dr. Carol Smith", "Dr", "Orthodontics"),
            ("Dan Kowalski", "RDT", "Denturist"),
            ("Eve Tremblay", "RDA", "Dental Assistant"),
            ("Frank Lee", "RDA", "Dental Assistant"),
        ]
        providers = []
        for name, title, specialty in provider_specs:
            existing = db.query(Provider).filter(
                Provider.clinic_id == DEFAULT_CLINIC_ID,
                Provider.name == name,
            ).first()
            if not existing:
                p = Provider(clinic_id=DEFAULT_CLINIC_ID, name=name, title=title,
                             specialty=specialty, is_active=True)
                db.add(p)
                db.flush()
                providers.append(p)
            else:
                providers.append(existing)

        # ── Patients ───────────────────────────────────────────────────────
        patients = []
        for _ in range(30):
            phone = fake.numerify("780#######")
            email = fake.unique.email()
            existing = db.query(Patient).filter(
                Patient.clinic_id == DEFAULT_CLINIC_ID,
                Patient.email == email,
            ).first()
            if not existing:
                p = Patient(
                    clinic_id=DEFAULT_CLINIC_ID,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone=phone,
                    email=email,
                    dob=fake.date_of_birth(minimum_age=18, maximum_age=85),
                )
                db.add(p)
                db.flush()
                patients.append(p)
            else:
                patients.append(existing)

        if not patients:
            patients = db.query(Patient).filter(Patient.clinic_id == DEFAULT_CLINIC_ID).limit(30).all()

        # ── Lab Vendors ────────────────────────────────────────────────────
        vendor_names = [
            "Precision Dental Lab", "Northern Crown Lab", "Pacific Prosthetics",
            "Maple Leaf Dental Lab", "Summit Ceramics",
        ]
        vendors = []
        for vname in vendor_names:
            existing = db.query(LabVendor).filter(
                LabVendor.clinic_id == DEFAULT_CLINIC_ID,
                LabVendor.name == vname,
            ).first()
            if not existing:
                v = LabVendor(
                    clinic_id=DEFAULT_CLINIC_ID,
                    name=vname,
                    contact_email=fake.email(),
                    contact_phone=fake.numerify("780#######"),
                    sla_days=random.choice([5, 7, 10, 14]),
                    is_active=True,
                )
                db.add(v)
                db.flush()
                vendors.append(v)
            else:
                vendors.append(existing)

        # ── Treatment Plans ────────────────────────────────────────────────
        tp_statuses = ["draft", "presented", "accepted", "in_progress", "completed", "declined", "draft", "accepted"]
        treatment_plans = []
        for i, status in enumerate(tp_statuses):
            patient = patients[i % len(patients)]
            tp = TreatmentPlan(
                clinic_id=DEFAULT_CLINIC_ID,
                patient_id=patient.id,
                status=status,
                total_estimate=round(random.uniform(500, 5000), 2),
                insurance_estimate=round(random.uniform(100, 2000), 2),
                patient_estimate=round(random.uniform(100, 2000), 2),
            )
            db.add(tp)
            db.flush()
            for seq in range(random.randint(2, 5)):
                item = TreatmentPlanItem(
                    plan_id=tp.id,
                    sequence=seq,
                    procedure_code=fake.bothify("##???"),
                    description=fake.sentence(nb_words=4),
                    fee=round(random.uniform(100, 1200), 2),
                    insurance_coverage_pct=random.choice([0, 50, 80]),
                    tooth_number=random.randint(11, 48) if random.random() > 0.3 else None,
                )
                db.add(item)
            treatment_plans.append(tp)
        db.flush()

        # ── Invoices ───────────────────────────────────────────────────────
        now = datetime.utcnow()
        invoice_statuses = (
            ["draft"] * 4 + ["issued"] * 8 + ["partial"] * 6 + ["paid"] * 6 + ["void"] * 1
        )
        for i, status in enumerate(invoice_statuses):
            patient = patients[i % len(patients)]
            days_ago = random.randint(0, 90)
            created = now - timedelta(days=days_ago)
            subtotal = round(random.uniform(200, 2000), 2)
            gst = round(subtotal * 0.05, 2)
            total = subtotal + gst
            balance = 0 if status == "paid" else (round(total * 0.5, 2) if status == "partial" else total)
            inv = Invoice(
                clinic_id=DEFAULT_CLINIC_ID,
                patient_id=patient.id,
                status=status,
                subtotal=subtotal,
                gst=gst,
                total=total,
                balance=balance,
                created_at=created,
                issued_at=created if status != "draft" else None,
            )
            db.add(inv)
            db.flush()
            line = InvoiceLine(
                invoice_id=inv.id,
                sequence=1,
                description=fake.sentence(nb_words=3),
                qty=1,
                unit_price=subtotal,
                total=subtotal,
            )
            db.add(line)

        # ── Communications ─────────────────────────────────────────────────
        channels = ["sms", "email", "whatsapp"]
        unread_budget = 8

        for i in range(65):
            patient = patients[i % len(patients)]
            channel = channels[i % len(channels)]
            thread_key = f"{patient.id}:{channel}"
            direction = "out" if i % 3 != 0 else "in"
            days_ago = random.randint(0, 30)
            created = now - timedelta(days=days_ago, hours=random.randint(0, 23))

            read_at = None
            if unread_budget > 0 and random.random() < 0.15:
                unread_budget -= 1
            else:
                read_at = created + timedelta(minutes=random.randint(5, 120))

            comm = Communication(
                clinic_id=DEFAULT_CLINIC_ID,
                patient_id=patient.id,
                channel=channel,
                direction=direction,
                body=fake.sentence(nb_words=random.randint(5, 20)),
                status="sent" if direction == "out" else "received",
                thread_key=thread_key,
                read_at=read_at,
                attachments=[],
                created_at=created,
                sent_at=created if direction == "out" else None,
            )
            db.add(comm)

        # ── Lab Cases ──────────────────────────────────────────────────────
        denture_cases = db.query(DentureCase).filter(DentureCase.clinic_id == DEFAULT_CLINIC_ID).limit(5).all()
        if not denture_cases:
            for j in range(5):
                patient = patients[j % len(patients)]
                dc = DentureCase(
                    clinic_id=DEFAULT_CLINIC_ID,
                    patient_id=patient.id,
                    arch=random.choice(["upper", "lower", "both"]),
                    case_type=random.choice(["complete", "partial", "immediate"]),
                    current_stage="consult",
                    status="open",
                )
                db.add(dc)
                db.flush()
                denture_cases.append(dc)

        lab_statuses = ["draft", "sent", "in_progress", "returned", "remake",
                        "draft", "sent", "in_progress", "returned", "remake", "sent", "returned"]
        for i, status in enumerate(lab_statuses):
            dc = denture_cases[i % len(denture_cases)]
            vendor = vendors[i % len(vendors)]
            case_num = next_lab_case_number(db, DEFAULT_CLINIC_ID)
            lc = LabCase(
                clinic_id=DEFAULT_CLINIC_ID,
                denture_case_id=dc.id,
                vendor_id=vendor.id,
                case_number=case_num,
                status=status,
                lab_fee=round(random.uniform(200, 800), 2),
                due_back_at=now + timedelta(days=random.randint(3, 21)) if status in ("sent", "in_progress") else None,
                sent_at=now - timedelta(days=random.randint(1, 14)) if status != "draft" else None,
                returned_at=now - timedelta(days=random.randint(0, 5)) if status in ("returned", "remake") else None,
                treatment_plan_id=treatment_plans[i % len(treatment_plans)].id if treatment_plans else None,
            )
            db.add(lc)

        # ── Leads ──────────────────────────────────────────────────────────
        lead_statuses = (
            [LeadStatus.NEW] * 5 + [LeadStatus.CONTACTED] * 4 +
            [LeadStatus.QUALIFIED] * 3 + [LeadStatus.CONVERTED] * 2 + [LeadStatus.LOST] * 1
        )
        sources = ["google_ads", "facebook", "referral", "walk_in", "website"]
        existing_lead_count = db.query(Lead).filter(Lead.clinic_id == DEFAULT_CLINIC_ID).count()
        for i, status in enumerate(lead_statuses):
            if existing_lead_count + i >= 15:
                break
            lead = Lead(
                clinic_id=DEFAULT_CLINIC_ID,
                name=fake.name(),
                phone=fake.numerify("780#######"),
                email=fake.email(),
                source=random.choice(sources),
                status=status,
                notes=fake.sentence(nb_words=8),
            )
            db.add(lead)

        db.commit()
        print("Demo clinic seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
