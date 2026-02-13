# Migration Guide: SQLite to PostgreSQL

Complete guide to migrate your SQLite database (`dental_clinic.db`) to PostgreSQL.

## Prerequisites

- Python 3.11+
- PostgreSQL database (local or cloud)
- SQLite database file (`dental_clinic.db`)
- Database connection string

## Step-by-Step Migration

### Step 1: Set Up PostgreSQL Database

Choose one option:

#### Option A: Vercel Postgres (For Vercel Deployment)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Storage → Create Database → Postgres
3. Copy the connection string
4. It will look like: `postgresql://default:password@host:5432/verceldb`

#### Option B: Supabase (Free Tier Available)

1. Go to [Supabase](https://supabase.com)
2. Create new project
3. Go to Settings → Database
4. Copy connection string (Connection Pooling)
5. Format: `postgresql://postgres:password@host:5432/postgres`

#### Option C: Neon (Free Tier Available)

1. Go to [Neon](https://neon.tech)
2. Create new project
3. Copy connection string
4. Format: `postgresql://user:password@host:5432/dbname`

#### Option D: Local PostgreSQL

```bash
# Using Docker
docker run -d \
  --name dental-postgres \
  -e POSTGRES_USER=dental_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=dental_clinic \
  -p 5432:5432 \
  postgres:15-alpine

# Connection string:
# postgresql://dental_user:your_password@localhost:5432/dental_clinic
```

### Step 2: Install Dependencies

```bash
cd dental-api

# Install Python dependencies
pip install -r requirements.txt

# Or using uv
uv sync
```

### Step 3: Set Database URL

```bash
# Set PostgreSQL connection string
export DATABASE_URL="postgresql://user:password@host:5432/dbname"

# For Vercel Postgres, Supabase, Neon (with SSL):
export DATABASE_URL="postgresql://user:password@host:5432/dbname?sslmode=require"
```

**Important:** Make sure `DATABASE_URL` points to PostgreSQL, not SQLite!

### Step 4: Locate SQLite Database

The migration script will look for `dental_clinic.db` in these locations:
1. Current directory (`./dental_clinic.db`)
2. Parent directory (`../dental_clinic.db`)
3. Project root

If your SQLite file is elsewhere, you can:
```bash
# Copy to project root
cp /path/to/dental_clinic.db ./dental_clinic.db

# Or create symlink
ln -s /path/to/dental_clinic.db ./dental_clinic.db
```

### Step 5: Run Migration

```bash
# Make sure you're in dental-api directory
cd dental-api

# Run migration script
python scripts/migrate_sqlite_to_postgres.py
```

### Step 6: Verify Migration

The script will automatically verify by comparing record counts:

```
🔍 Verifying migration...
  ✓ doctors: SQLite=3, PostgreSQL=3
  ✓ services: SQLite=70, PostgreSQL=70
  ✓ patients: SQLite=25, PostgreSQL=25
  ✓ appointments: SQLite=10, PostgreSQL=10
  ✓ leads: SQLite=5, PostgreSQL=5

✅ Migration verification passed!
```

### Step 7: Test PostgreSQL Connection

```bash
# Test connection
python -c "from database.connection import engine; engine.connect(); print('✓ Connection successful')"

# Or run API locally
uvicorn api.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/doctors
curl http://localhost:8000/api/patients
```

## Migration Script Details

The migration script (`migrate_sqlite_to_postgres.py`) does the following:

1. **Connects to SQLite** - Reads from `dental_clinic.db`
2. **Connects to PostgreSQL** - Uses `DATABASE_URL` environment variable
3. **Creates tables** - Creates all tables in PostgreSQL
4. **Migrates data** - Copies all data preserving:
   - IDs (UUIDs)
   - Relationships (foreign keys)
   - Dates and timestamps
   - Enums (status fields)
   - All other fields
5. **Verifies** - Compares record counts

### Tables Migrated

- ✅ `doctors` - Doctor information
- ✅ `services` - Dental services
- ✅ `patients` - Patient records
- ✅ `appointments` - Appointment records
- ✅ `leads` - Lead records (if exists)

### Data Preserved

- All IDs (UUIDs preserved)
- All relationships (foreign keys)
- Dates and timestamps
- Status enums (converted properly)
- All text fields
- Boolean fields

## Troubleshooting

### Error: "DATABASE_URL environment variable not set"

```bash
# Set it before running migration
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
python scripts/migrate_sqlite_to_postgres.py
```

### Error: "SQLite database not found"

```bash
# Check if file exists
ls -la dental_clinic.db

# Or specify full path in script
# Edit migrate_sqlite_to_postgres.py line ~30
sqlite_path = "/full/path/to/dental_clinic.db"
```

### Error: "Connection refused" or "Could not connect"

- Check PostgreSQL is running
- Verify connection string format
- Check firewall/network settings
- For cloud databases, ensure IP whitelist allows your IP

### Error: "relation already exists"

The script checks for existing records and skips them. If you want to start fresh:

```bash
# Drop all tables (CAREFUL - deletes all data!)
python -c "from database.connection import Base, engine; Base.metadata.drop_all(bind=engine)"

# Then run migration again
python scripts/migrate_sqlite_to_postgres.py
```

### Error: "Invalid date format"

The script handles various date formats. If you see date parsing errors:
- Check the SQLite database for invalid dates
- The script will skip records with invalid dates and continue

### Partial Migration

If migration fails partway:
- The script uses transactions, so partial migrations are rolled back
- Fix the issue and run again
- Existing records are skipped (won't duplicate)

## After Migration

### 1. Update Environment Variables

**Local Development:**
```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost:5432/dental_clinic
```

**Vercel Deployment:**
```bash
# Set in Vercel Dashboard → Settings → Environment Variables
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
```

### 2. Backup SQLite Database (Keep as Backup)

```bash
# Create backup
cp dental_clinic.db dental_clinic_backup_$(date +%Y%m%d).db

# Or compress
tar -czf dental_clinic_backup.tar.gz dental_clinic.db
```

### 3. Test Everything

```bash
# Test API endpoints
curl http://localhost:8000/api/patients
curl http://localhost:8000/api/appointments
curl http://localhost:8000/api/doctors

# Test creating new records
curl -X POST http://localhost:8000/api/patients \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Test", "last_name": "User"}'
```

### 4. Deploy to Vercel

Once migration is complete and tested locally:

```bash
# Deploy with PostgreSQL
vercel deploy --prod

# Verify on Vercel
curl https://your-app.vercel.app/health
```

## Migration Checklist

- [ ] PostgreSQL database created
- [ ] `DATABASE_URL` set correctly
- [ ] SQLite database file located
- [ ] Dependencies installed
- [ ] Migration script run successfully
- [ ] Verification passed (record counts match)
- [ ] Tested API endpoints locally
- [ ] Updated environment variables
- [ ] Backed up SQLite database
- [ ] Deployed to Vercel (if applicable)

## Quick Reference

```bash
# 1. Set PostgreSQL URL
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# 2. Run migration
cd dental-api
python scripts/migrate_sqlite_to_postgres.py

# 3. Verify
python -c "from database.connection import SessionLocal; from database.models import Patient; print(f'Patients: {SessionLocal().query(Patient).count()}')"

# 4. Test API
uvicorn api.main:app --reload
```

## Need Help?

- Check migration script logs for specific errors
- Verify PostgreSQL connection string format
- Ensure all dependencies are installed
- Check PostgreSQL logs for connection issues

## Next Steps

After successful migration:
1. ✅ Test all API endpoints
2. ✅ Update agent `CALENDAR_API_URL` to point to deployed API
3. ✅ Deploy API to Vercel
4. ✅ Deploy agent to LiveKit Cloud
