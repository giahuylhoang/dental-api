# Quick Migration Guide - Using .env.local

Since you've saved your Supabase credentials in `.env.local`, here's the quickest way to migrate:

## Step 1: Install Dependencies

```bash
cd dental-api
pip install -r requirements.txt
```

This will install `python-dotenv` which is needed to load `.env.local`.

## Step 2: Verify .env.local

Make sure your `.env.local` file is in the `dental-api/` directory and contains:

```bash
DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
```

**Check it:**
```bash
cd dental-api
cat .env.local | grep DATABASE_URL
```

## Step 3: Run Migration

```bash
cd dental-api
python scripts/migrate_sqlite_to_postgres.py
```

That's it! The script will:
- ✅ Automatically load `DATABASE_URL` from `.env.local`
- ✅ Connect to your Supabase database
- ✅ Migrate all your data
- ✅ Verify the migration

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

🔍 Verifying migration...
  ✓ doctors: SQLite=3, PostgreSQL=3
  ✓ services: SQLite=70, PostgreSQL=70
  ✓ patients: SQLite=25, PostgreSQL=25
  ✓ appointments: SQLite=10, PostgreSQL=10

✅ Migration verification passed!
✅ Migration completed successfully!
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"

```bash
pip install python-dotenv
```

### "DATABASE_URL environment variable not set"

Check that `.env.local`:
1. Is in `dental-api/` directory (not parent directory)
2. Contains `DATABASE_URL=` (no spaces)
3. Has the connection string in quotes

```bash
# Verify file location
ls -la dental-api/.env.local

# Check contents
cat dental-api/.env.local
```

### Connection Errors

Make sure you're using port **5432** (direct connection) for migrations, not 6543 (pooled).

## After Migration

Test your API:

```bash
# Start API
uvicorn api.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/patients
```

## Next: Deploy to Vercel

After migration works locally, deploy to Vercel:

1. Set `DATABASE_URL` in Vercel Dashboard (use port **6543** for production)
2. Deploy: `vercel deploy --prod`

Done! 🎉
