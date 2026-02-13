# Quick Migration to Supabase

## Step 1: Set Database URL

```bash
cd dental-api

# Set environment variable
export DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
```

Or create `.env` file:
```bash
echo 'DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"' > .env
```

## Step 2: Test Connection

```bash
python -c "from database.connection import engine; engine.connect(); print('✓ Supabase connection successful!')"
```

## Step 3: Run Migration

```bash
python scripts/migrate_sqlite_to_postgres.py
```

## Step 4: Verify

The script will show:
```
🔍 Verifying migration...
  ✓ doctors: SQLite=X, PostgreSQL=X
  ✓ services: SQLite=X, PostgreSQL=X
  ✓ patients: SQLite=X, PostgreSQL=X
  ✓ appointments: SQLite=X, PostgreSQL=X
```

## Step 5: Test API

```bash
# Start API
uvicorn api.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/doctors
curl http://localhost:8000/api/patients
```

## For Vercel Deployment

Set in Vercel Dashboard → Settings → Environment Variables:

**Use pooled connection for production:**
```
DATABASE_URL=postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

**Note:** Port 6543 is for pooled connections (better for production), port 5432 is for direct connections (better for migrations).

## Done! 🎉

Your data is now in Supabase PostgreSQL and ready for deployment.
