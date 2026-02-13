"""Database initialization script - creates tables and seeds initial data."""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.connection import init_db, SessionLocal
from database.models import Doctor, Service
from scripts.service_descriptions import SERVICE_DESCRIPTIONS


def seed_initial_data():
    """Seed initial data: doctors and services."""
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_doctors = db.query(Doctor).count()
        if existing_doctors > 0:
            print("Database already has data. Skipping seed.")
            return
        
        # Seed Doctors (matching doctor_calendars.py names)
        doctors = [
            Doctor(id=1, name="Dr. Johnson", specialty="General", is_active=True),
            Doctor(id=2, name="Dr. Smith", specialty="General", is_active=True),
            Doctor(id=3, name="Dr. Ahmed", specialty="General", is_active=True),
        ]
        for doctor in doctors:
            db.add(doctor)
        
        # Seed Services - Comprehensive dental clinic services
        services = [
            # Preventive Care
            Service(id=1, name="Routine Cleaning", description=SERVICE_DESCRIPTIONS.get(1), duration_min=60, base_price=150.00),
            Service(id=2, name="Deep Cleaning (Scaling & Root Planing)", description=SERVICE_DESCRIPTIONS.get(2), duration_min=90, base_price=250.00),
            Service(id=3, name="Dental Exam", description=SERVICE_DESCRIPTIONS.get(3), duration_min=30, base_price=100.00),
            Service(id=4, name="Comprehensive Oral Evaluation", description=SERVICE_DESCRIPTIONS.get(4), duration_min=45, base_price=150.00),
            Service(id=5, name="Periodic Oral Evaluation", description=SERVICE_DESCRIPTIONS.get(5), duration_min=20, base_price=75.00),
            Service(id=6, name="Fluoride Treatment", description=SERVICE_DESCRIPTIONS.get(6), duration_min=15, base_price=50.00),
            Service(id=7, name="Dental Sealants", description=SERVICE_DESCRIPTIONS.get(7), duration_min=30, base_price=80.00),
            
            # Diagnostic Services
            Service(id=8, name="X-Ray (Bitewing)", description=SERVICE_DESCRIPTIONS.get(8), duration_min=15, base_price=75.00),
            Service(id=9, name="X-Ray (Full Mouth Series)", description=SERVICE_DESCRIPTIONS.get(9), duration_min=30, base_price=150.00),
            Service(id=10, name="X-Ray (Panoramic)", description=SERVICE_DESCRIPTIONS.get(10), duration_min=20, base_price=120.00),
            Service(id=11, name="X-Ray (Periapical)", description=SERVICE_DESCRIPTIONS.get(11), duration_min=10, base_price=50.00),
            Service(id=12, name="Digital X-Ray", description=SERVICE_DESCRIPTIONS.get(12), duration_min=15, base_price=85.00),
            Service(id=13, name="3D Imaging (CBCT)", description=SERVICE_DESCRIPTIONS.get(13), duration_min=30, base_price=300.00),
            
            # Restorative Services
            Service(id=14, name="Filling (Amalgam)", description=SERVICE_DESCRIPTIONS.get(14), duration_min=60, base_price=200.00),
            Service(id=15, name="Filling (Composite)", description=SERVICE_DESCRIPTIONS.get(15), duration_min=60, base_price=250.00),
            Service(id=16, name="Filling (Ceramic)", description=SERVICE_DESCRIPTIONS.get(16), duration_min=75, base_price=350.00),
            Service(id=17, name="Crown (Porcelain)", description=SERVICE_DESCRIPTIONS.get(17), duration_min=90, base_price=1200.00),
            Service(id=18, name="Crown (Porcelain Fused to Metal)", description=SERVICE_DESCRIPTIONS.get(18), duration_min=90, base_price=1100.00),
            Service(id=19, name="Crown (Zirconia)", description=SERVICE_DESCRIPTIONS.get(19), duration_min=90, base_price=1400.00),
            Service(id=20, name="Crown (Gold)", description=SERVICE_DESCRIPTIONS.get(20), duration_min=90, base_price=1300.00),
            Service(id=21, name="Bridge (3-unit)", description=SERVICE_DESCRIPTIONS.get(21), duration_min=120, base_price=2500.00),
            Service(id=22, name="Inlay", description=SERVICE_DESCRIPTIONS.get(22), duration_min=75, base_price=800.00),
            Service(id=23, name="Onlay", description=SERVICE_DESCRIPTIONS.get(23), duration_min=90, base_price=950.00),
            
            # Endodontic Services
            Service(id=24, name="Root Canal (Anterior)", description=SERVICE_DESCRIPTIONS.get(24), duration_min=90, base_price=800.00),
            Service(id=25, name="Root Canal (Premolar)", description=SERVICE_DESCRIPTIONS.get(25), duration_min=120, base_price=900.00),
            Service(id=26, name="Root Canal (Molar)", description=SERVICE_DESCRIPTIONS.get(26), duration_min=150, base_price=1200.00),
            Service(id=27, name="Root Canal Retreatment", description=SERVICE_DESCRIPTIONS.get(27), duration_min=120, base_price=1000.00),
            Service(id=28, name="Apicoectomy", description=SERVICE_DESCRIPTIONS.get(28), duration_min=90, base_price=600.00),
            
            # Oral Surgery
            Service(id=29, name="Tooth Extraction (Simple)", description=SERVICE_DESCRIPTIONS.get(29), duration_min=30, base_price=200.00),
            Service(id=30, name="Tooth Extraction (Surgical)", description=SERVICE_DESCRIPTIONS.get(30), duration_min=60, base_price=400.00),
            Service(id=31, name="Wisdom Tooth Extraction", description=SERVICE_DESCRIPTIONS.get(31), duration_min=90, base_price=500.00),
            Service(id=32, name="Impacted Tooth Removal", description=SERVICE_DESCRIPTIONS.get(32), duration_min=120, base_price=800.00),
            Service(id=33, name="Bone Grafting", description=SERVICE_DESCRIPTIONS.get(33), duration_min=90, base_price=600.00),
            Service(id=34, name="Sinus Lift", description=SERVICE_DESCRIPTIONS.get(34), duration_min=120, base_price=1500.00),
            
            # Periodontic Services
            Service(id=35, name="Gum Disease Treatment", description=SERVICE_DESCRIPTIONS.get(35), duration_min=60, base_price=300.00),
            Service(id=36, name="Gingival Grafting", description=SERVICE_DESCRIPTIONS.get(36), duration_min=90, base_price=800.00),
            Service(id=37, name="Periodontal Maintenance", description=SERVICE_DESCRIPTIONS.get(37), duration_min=60, base_price=180.00),
            Service(id=38, name="Pocket Reduction Surgery", description=SERVICE_DESCRIPTIONS.get(38), duration_min=120, base_price=1000.00),
            
            # Cosmetic Services
            Service(id=39, name="Teeth Whitening (In-Office)", description=SERVICE_DESCRIPTIONS.get(39), duration_min=90, base_price=500.00),
            Service(id=40, name="Teeth Whitening (Take-Home Kit)", description=SERVICE_DESCRIPTIONS.get(40), duration_min=30, base_price=300.00),
            Service(id=41, name="Veneers (Porcelain)", description=SERVICE_DESCRIPTIONS.get(41), duration_min=120, base_price=1200.00),
            Service(id=42, name="Veneers (Composite)", description=SERVICE_DESCRIPTIONS.get(42), duration_min=90, base_price=600.00),
            Service(id=43, name="Bonding", description=SERVICE_DESCRIPTIONS.get(43), duration_min=60, base_price=400.00),
            Service(id=44, name="Gum Contouring", description=SERVICE_DESCRIPTIONS.get(44), duration_min=60, base_price=500.00),
            
            # Orthodontic Services
            Service(id=45, name="Orthodontic Consultation", description=SERVICE_DESCRIPTIONS.get(45), duration_min=60, base_price=150.00),
            Service(id=46, name="Traditional Braces", description=SERVICE_DESCRIPTIONS.get(46), duration_min=90, base_price=5000.00),
            Service(id=47, name="Invisalign", description=SERVICE_DESCRIPTIONS.get(47), duration_min=60, base_price=5500.00),
            Service(id=48, name="Retainer", description=SERVICE_DESCRIPTIONS.get(48), duration_min=30, base_price=300.00),
            Service(id=49, name="Braces Adjustment", description=SERVICE_DESCRIPTIONS.get(49), duration_min=30, base_price=100.00),
            
            # Prosthodontic Services
            Service(id=50, name="Dentures (Full Set)", description=SERVICE_DESCRIPTIONS.get(50), duration_min=180, base_price=2000.00),
            Service(id=51, name="Dentures (Partial)", description=SERVICE_DESCRIPTIONS.get(51), duration_min=120, base_price=1500.00),
            Service(id=52, name="Denture Reline", description=SERVICE_DESCRIPTIONS.get(52), duration_min=60, base_price=300.00),
            Service(id=53, name="Denture Repair", description=SERVICE_DESCRIPTIONS.get(53), duration_min=45, base_price=200.00),
            Service(id=54, name="Implant Consultation", description=SERVICE_DESCRIPTIONS.get(54), duration_min=60, base_price=200.00),
            Service(id=55, name="Dental Implant (Single)", description=SERVICE_DESCRIPTIONS.get(55), duration_min=120, base_price=3000.00),
            Service(id=56, name="Implant Crown", description=SERVICE_DESCRIPTIONS.get(56), duration_min=90, base_price=1500.00),
            
            # Pediatric Services
            Service(id=57, name="Child's Cleaning", description=SERVICE_DESCRIPTIONS.get(57), duration_min=45, base_price=100.00),
            Service(id=58, name="Child's Exam", description=SERVICE_DESCRIPTIONS.get(58), duration_min=30, base_price=75.00),
            Service(id=59, name="Baby Tooth Extraction", description=SERVICE_DESCRIPTIONS.get(59), duration_min=30, base_price=150.00),
            Service(id=60, name="Space Maintainer", description=SERVICE_DESCRIPTIONS.get(60), duration_min=60, base_price=400.00),
            
            # Emergency Services
            Service(id=61, name="Emergency Visit", description=SERVICE_DESCRIPTIONS.get(61), duration_min=60, base_price=200.00),
            Service(id=62, name="Toothache Treatment", description=SERVICE_DESCRIPTIONS.get(62), duration_min=45, base_price=150.00),
            Service(id=63, name="Broken Tooth Repair", description=SERVICE_DESCRIPTIONS.get(63), duration_min=60, base_price=250.00),
            Service(id=64, name="Lost Filling/Crown", description=SERVICE_DESCRIPTIONS.get(64), duration_min=45, base_price=200.00),
            
            # Specialized Services
            Service(id=65, name="TMJ Treatment", description=SERVICE_DESCRIPTIONS.get(65), duration_min=60, base_price=300.00),
            Service(id=66, name="Sleep Apnea Consultation", description=SERVICE_DESCRIPTIONS.get(66), duration_min=60, base_price=200.00),
            Service(id=67, name="Oral Cancer Screening", description=SERVICE_DESCRIPTIONS.get(67), duration_min=30, base_price=100.00),
            Service(id=68, name="Nitrous Oxide (Laughing Gas)", description=SERVICE_DESCRIPTIONS.get(68), duration_min=0, base_price=50.00),
            Service(id=69, name="IV Sedation", description=SERVICE_DESCRIPTIONS.get(69), duration_min=0, base_price=400.00),
            
            # General/Unknown Services
            Service(id=70, name="General Consultation", description=SERVICE_DESCRIPTIONS.get(70), duration_min=30, base_price=100.00),
        ]
        for service in services:
            db.add(service)
        
        db.commit()
        print(f"✓ Seeded {len(doctors)} doctors and {len(services)} services")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("✓ Database tables created")
    
    print("Seeding initial data...")
    seed_initial_data()
    print("✓ Database initialization complete!")
