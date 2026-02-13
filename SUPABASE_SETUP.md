# Supabase Setup for Dental API

Your Supabase PostgreSQL connection details.

## Connection Strings

### For Migrations (Direct Connection - Recommended)
```bash
DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
```

### For Production (Pooled Connection - Better Performance)
```bash
DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
```

**Note:** Use direct connection (port 5432) for migrations, pooled connection (port 6543) for production.

## Quick Setup

### 1. Set Environment Variable

```bash
# For migration (direct connection)
export DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

# Or add to .env file
echo 'DATABASE_URL="postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"' >> .env
```

### 2. Test Connection

```bash
python -c "from database.connection import engine; engine.connect(); print('✓ Connection successful')"
```

### 3. Run Migration

```bash
python scripts/migrate_sqlite_to_postgres.py
```

## For Vercel Deployment

Set these environment variables in Vercel Dashboard:

**For Production (Pooled):**
```
DATABASE_URL=postgresql://postgres.ivkfrvrgipqkixmewjbn:c0RB8g32jGO1zTuS@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

**Optional Supabase Variables (if needed):**
```
SUPABASE_URL=https://ivkfrvrgipqkixmewjbn.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2a2ZydnJnaXBxa2l4bWV3amJuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjcyNjkwNSwiZXhwIjoyMDgyMzAyOTA1fQ.zoM_do65qbTz-5M5_0qC0coxfIA8DHnJEYLFAy8xlFg
```

## Security Notes

⚠️ **Important:** These credentials are sensitive. Never commit them to git!

- Add `.env` to `.gitignore`
- Use Vercel environment variables for production
- Rotate keys if exposed

## Connection Details

- **Host:** `aws-1-us-east-1.pooler.supabase.com`
- **Port (Direct):** `5432`
- **Port (Pooled):** `6543`
- **Database:** `postgres`
- **User:** `postgres.ivkfrvrgipqkixmewjbn`
- **SSL:** Required (`sslmode=require`)
