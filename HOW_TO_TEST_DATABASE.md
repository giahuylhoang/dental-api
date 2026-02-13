# How to Check if Your Database is Working

Multiple ways to verify your database connection is working correctly.

## Method 1: Quick Test Script (Recommended)

Run the test script:

```bash
cd dental-api
python test_database.py
```

This will:
- ✅ Test database connection
- ✅ Verify all tables exist
- ✅ Test read/write operations
- ✅ Show database statistics

**Expected Output:**
```
============================================================
Database Connection Test
============================================================

🔍 Testing database connection...
📊 Database URL: postgresql://...
✅ Database connection successful!

🔍 Testing database tables...
   ✅ patients: 38 records
   ✅ doctors: 31 records
   ✅ services: 93 records
   ✅ appointments: 37 records

✅ All tests passed! Your database is working correctly.
```

## Method 2: Test via Python REPL

Quick interactive test:

```bash
cd dental-api
python3
```

Then in Python:

```python
from database.connection import engine, SessionLocal, DATABASE_URL
from database.models import Patient, Doctor

# Check connection URL
print(f"Database URL: {DATABASE_URL}")

# Test connection
with engine.connect() as conn:
    print("✅ Connection successful!")

# Test query
session = SessionLocal()
try:
    patient_count = session.query(Patient).count()
    doctor_count = session.query(Doctor).count()
    print(f"✅ Found {patient_count} patients and {doctor_count} doctors")
finally:
    session.close()
```

## Method 3: Test via API Endpoint

If your API is running, test via HTTP:

```bash
# Start API server
cd dental-api
python api/main.py
# or
uvicorn api.main:app --reload
```

Then in another terminal:

```bash
# Test health endpoint (if you have one)
curl http://localhost:8000/health

# Or test a database endpoint
curl http://localhost:8000/api/patients
curl http://localhost:8000/api/doctors
```

## Method 4: Direct PostgreSQL Connection Test

Test PostgreSQL connection directly (bypassing SQLAlchemy):

```bash
# Install psql if not installed
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql-client

# Extract connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/database

# Connect directly
psql "postgresql://user:password@host:5432/database"
```

Or use Python:

```bash
python3 -c "
import os
from urllib.parse import urlparse

db_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL', '')
if db_url:
    parsed = urlparse(db_url)
    print(f'Host: {parsed.hostname}')
    print(f'Port: {parsed.port}')
    print(f'Database: {parsed.path[1:]}')
    print(f'User: {parsed.username}')
"
```

## Method 5: Check Environment Variables

Verify your database URL is set correctly:

```bash
# Check environment variables
cd dental-api

# If using .env.local
cat .env.local | grep -E "DATABASE_URL|POSTGRES_URL"

# Or check in Python
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')
print('DATABASE_URL:', os.getenv('DATABASE_URL', 'NOT SET')[:50])
print('POSTGRES_URL:', os.getenv('POSTGRES_URL', 'NOT SET')[:50])
"
```

## Method 6: Test Database Operations

Create a simple test script:

```python
# test_simple.py
import os
from database.connection import SessionLocal
from database.models import Patient, Doctor

session = SessionLocal()
try:
    # Test read
    patients = session.query(Patient).limit(5).all()
    print(f"✅ Read test: Found {len(patients)} patients")
    
    # Test write (optional - creates a test record)
    # Uncomment if you want to test writes:
    # from datetime import datetime
    # test_doctor = Doctor(name="Test Doctor", specialty="Test")
    # session.add(test_doctor)
    # session.commit()
    # print("✅ Write test: Created test doctor")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    session.close()
```

Run it:
```bash
python test_simple.py
```

## Troubleshooting

### Error: "Can't load plugin: sqlalchemy.dialects:postgres"

**Solution:** Install PostgreSQL driver:

```bash
# Activate virtual environment first
source .venv/bin/activate  # or your venv path

# Install PostgreSQL driver
pip install psycopg2-binary

# Or install all requirements
pip install -r requirements.txt
```

### Error: "Connection refused" or "Could not connect"

**Check:**
1. ✅ Database server is running
2. ✅ Connection string is correct
3. ✅ Network/firewall allows connection
4. ✅ Database credentials are valid

**For Vercel Postgres:**
- Check Vercel Dashboard → Storage → Your Database
- Verify database is not paused
- Check region matches deployment region

**For External PostgreSQL:**
- Verify connection string format
- Check SSL mode if required (`?sslmode=require`)
- Test connection from command line with `psql`

### Error: "No such table: patients"

**Solution:** Initialize database:

```bash
cd dental-api
python scripts/init_database.py
```

Or if migrating from SQLite:

```bash
python scripts/migrate_sqlite_to_postgres.py
```

### Error: "DATABASE_URL not set"

**Solution:** Set environment variable:

```bash
# For local development
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Or add to .env.local
echo 'DATABASE_URL="postgresql://..."' >> .env.local

# For Vercel
vercel env add DATABASE_URL production
```

## Quick Checklist

- [ ] Database server is running
- [ ] Environment variable is set (`DATABASE_URL` or `POSTGRES_URL`)
- [ ] PostgreSQL driver installed (`psycopg2-binary`)
- [ ] Can connect to database
- [ ] Tables exist (run `init_database.py` if not)
- [ ] Can read from database
- [ ] Can write to database (optional test)

## Expected Results

When everything is working, you should see:

✅ **Connection successful**
✅ **Tables exist and are accessible**
✅ **Can query data**
✅ **Record counts match your expectations**

If you see errors, check the troubleshooting section above or the error message for specific guidance.
