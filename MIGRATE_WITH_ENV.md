# Migration Using .env.local

If you've saved your Supabase credentials in `.env.local`, here's how to migrate:

## Step 1: Verify .env.local File

Make sure your `.env.local` file contains:

```bash
DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
```

**Location:** Place `.env.local` in the `dental-api/` directory (same level as `scripts/` folder).

## Step 2: Install python-dotenv (If Not Already Installed)

The migration script uses `python-dotenv` to load `.env.local`:

```bash
pip install python-dotenv
# Or if using requirements.txt, it's already included
pip install -r requirements.txt
```

## Step 3: Run Migration

```bash
cd dental-api

# The script will automatically load from .env.local
python scripts/migrate_sqlite_to_postgres.py
```

The script will:
1. ✅ Look for `.env.local` file
2. ✅ Load `DATABASE_URL` from it
3. ✅ Connect to Supabase
4. ✅ Migrate all data

## What You'll See

```
✓ Loaded environment from: /path/to/dental-api/.env.local
============================================================
SQLite to PostgreSQL Migration
============================================================

📊 PostgreSQL URL: aws-1-us-east-1.pooler.supabase.com:5432/postgres
✓ PostgreSQL connection successful

📋 Creating PostgreSQL tables...
✓ Tables created

👨‍⚕️ Migrating doctors...
✓ Migrated 3 doctors

🦷 Migrating services...
✓ Migrated 70 services

👤 Migrating patients...
✓ Migrated 25 patients

📅 Migrating appointments...
✓ Migrated 10 appointments

📞 Migrating leads...
✓ Migrated 5 leads

🔍 Verifying migration...
  ✓ doctors: SQLite=3, PostgreSQL=3
  ✓ services: SQLite=70, PostgreSQL=70
  ✓ patients: SQLite=25, PostgreSQL=25
  ✓ appointments: SQLite=10, PostgreSQL=10
  ✓ leads: SQLite=5, PostgreSQL=5

✅ Migration verification passed!

============================================================
✅ Migration completed successfully!
============================================================
```

## Troubleshooting

### Error: "DATABASE_URL environment variable not set"

**Solution:** Check that `.env.local` file:
1. Exists in `dental-api/` directory
2. Contains `DATABASE_URL=` (no spaces around `=`)
3. Has the connection string in quotes

**Verify file:**
```bash
cd dental-api
cat .env.local | grep DATABASE_URL
```

### Error: "ModuleNotFoundError: No module named 'dotenv'"

**Solution:** Install python-dotenv:
```bash
pip install python-dotenv
```

### Error: "Could not connect to PostgreSQL"

**Solution:** 
1. Verify your Supabase credentials are correct
2. Check that your IP is allowed (Supabase dashboard → Settings → Database → Connection Pooling)
3. Try the connection string with port 5432 (direct) instead of 6543 (pooled)

## File Structure

```
dental-api/
├── .env.local          ← Your credentials here
├── scripts/
│   └── migrate_sqlite_to_postgres.py
├── database/
└── ...
```

## Security Note

⚠️ **Never commit `.env.local` to git!**

Make sure `.env.local` is in `.gitignore`:

```bash
# Check .gitignore
cat .gitignore | grep env

# If not there, add it:
echo ".env.local" >> .gitignore
echo ".env" >> .gitignore
```

## After Migration

1. ✅ Test locally:
   ```bash
   uvicorn api.main:app --reload
   curl http://localhost:8000/api/patients
   ```

2. ✅ Deploy to Vercel:
   - Set `DATABASE_URL` in Vercel Dashboard
   - Use pooled connection (port 6543) for production

3. ✅ Verify on Supabase:
   - Go to Supabase Dashboard → Table Editor
   - You should see all your tables and data

## Quick Reference

```bash
# 1. Ensure .env.local exists with DATABASE_URL
cd dental-api
cat .env.local

# 2. Run migration
python scripts/migrate_sqlite_to_postgres.py

# 3. Verify
python -c "from database.connection import SessionLocal; from database.models import Patient; print(f'Patients: {SessionLocal().query(Patient).count()}')"
```

That's it! The migration script will automatically use your `.env.local` file. 🎉
