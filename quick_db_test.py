#!/usr/bin/env python3
"""
Quick database test - minimal dependencies.
Tests if database connection string is configured correctly.
"""

import os
import sys
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

def check_database_url():
    """Check if database URL is configured."""
    print("🔍 Checking database configuration...\n")
    
    # Check for various database URL variables
    db_url = (
        os.getenv("POSTGRES_URL") or
        os.getenv("POSTGRES_PRISMA_URL") or
        os.getenv("POSTGRES_URL_NON_POOLING") or
        os.getenv("DATABASE_URL")
    )
    
    if not db_url:
        print("❌ No database URL found!")
        print("\nSet one of these environment variables:")
        print("  - POSTGRES_URL (Vercel Postgres)")
        print("  - DATABASE_URL (Custom PostgreSQL)")
        print("\nOr create .env.local file with:")
        print('  DATABASE_URL="postgresql://user:pass@host:5432/dbname"')
        return False
    
    # Show URL (masked)
    if len(db_url) > 60:
        masked_url = db_url[:30] + "..." + db_url[-30:]
    else:
        masked_url = db_url
    
    print(f"✅ Database URL found: {masked_url}")
    
    # Check URL format
    if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
        print("✅ Valid PostgreSQL connection string")
        return True
    elif db_url.startswith("sqlite://"):
        print("⚠️  Using SQLite (works locally, not on Vercel)")
        return True
    else:
        print("⚠️  Unknown database URL format")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n🔍 Checking dependencies...\n")
    
    missing = []
    
    # Check SQLAlchemy
    try:
        import sqlalchemy
        print("✅ sqlalchemy installed")
    except ImportError:
        print("❌ sqlalchemy NOT installed")
        missing.append("sqlalchemy")
    
    # Check PostgreSQL driver
    try:
        import psycopg2
        print("✅ psycopg2-binary installed")
    except ImportError:
        print("❌ psycopg2-binary NOT installed")
        missing.append("psycopg2-binary")
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install psycopg2-binary")
        print("  # or")
        print("  pip install -r requirements.txt")
        return False
    
    return True

def test_connection():
    """Test actual database connection."""
    print("\n🔍 Testing database connection...\n")
    
    try:
        from database.connection import engine, SessionLocal, DATABASE_URL
        from database.models import Patient, Doctor
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")
        
        # Test query
        session = SessionLocal()
        try:
            patient_count = session.query(Patient).count()
            doctor_count = session.query(Doctor).count()
            print(f"✅ Query test successful!")
            print(f"   Found {patient_count} patients and {doctor_count} doctors")
        finally:
            session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\nPossible issues:")
        print("  1. Database server not running")
        print("  2. Invalid connection credentials")
        print("  3. Network/firewall blocking connection")
        print("  4. Database doesn't exist")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print()
    
    # Step 1: Check configuration
    config_ok = check_database_url()
    if not config_ok:
        print("\n❌ Configuration check failed. Please set DATABASE_URL.")
        return 1
    
    # Step 2: Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n⚠️  Dependencies missing. Install them to test connection.")
        return 1
    
    # Step 3: Test connection
    conn_ok = test_connection()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"  Dependencies:  {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"  Connection:    {'✅ PASS' if conn_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if config_ok and deps_ok and conn_ok:
        print("\n✅ All tests passed! Your database is working correctly.")
        return 0
    elif config_ok and deps_ok:
        print("\n⚠️  Configuration and dependencies OK, but connection failed.")
        print("   Check database server and network connectivity.")
        return 1
    else:
        print("\n⚠️  Some checks failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
