# Using Vercel Postgres (No DATABASE_URL Needed!)

Great news! If you're using **Vercel Postgres**, you don't need to manually set `DATABASE_URL`. Vercel automatically provides the connection string.

## How It Works

When you create a Vercel Postgres database, Vercel automatically creates these environment variables:

- `POSTGRES_URL` - Direct connection string
- `POSTGRES_PRISMA_URL` - Prisma-compatible connection string  
- `POSTGRES_URL_NON_POOLING` - Non-pooling connection string

The application code automatically detects and uses these variables!

## Setup Steps

### 1. Create Vercel Postgres Database

1. Go to Vercel Dashboard → Your Project → **Storage** tab
2. Click **Create Database** → **Postgres**
3. Choose a name (e.g., "dental-clinic-db")
4. Select a region
5. Click **Create**

Vercel automatically:
- ✅ Creates the database
- ✅ Adds connection strings to your environment variables
- ✅ Makes them available to your application

### 2. Verify Environment Variables

The variables are automatically added, but you can verify:

1. Go to **Settings** → **Environment Variables**
2. You should see:
   - `POSTGRES_URL`
   - `POSTGRES_PRISMA_URL`
   - `POSTGRES_URL_NON_POOLING`

### 3. Deploy or Redeploy

```bash
# If already deployed, trigger a new deployment
vercel deploy --prod

# Or push to trigger automatic deployment
git push
```

### 4. Initialize Database (First Time)

After deployment, initialize your database schema:

```bash
# Pull environment variables locally
vercel env pull .env.local

# Run initialization
python scripts/init_database.py
```

Or if you're migrating from SQLite:

```bash
# Pull environment variables
vercel env pull .env.local

# Run migration
python scripts/migrate_sqlite_to_postgres.py
```

## Environment Variable Priority

The application checks for database URLs in this order:

1. `POSTGRES_URL` (Vercel Postgres direct)
2. `POSTGRES_PRISMA_URL` (Vercel Postgres Prisma)
3. `POSTGRES_URL_NON_POOLING` (Vercel Postgres non-pooling)
4. `DATABASE_URL` (Custom/External PostgreSQL)
5. `sqlite:///./dental_clinic.db` (Local development fallback)

## When You Still Need DATABASE_URL

You only need to manually set `DATABASE_URL` if:

- ❌ Using **external PostgreSQL** (Supabase, Neon, Railway, etc.)
- ❌ Using **custom PostgreSQL** server
- ❌ **Not using Vercel Postgres**

## Using External PostgreSQL Instead

If you're using Supabase, Neon, or another PostgreSQL provider:

1. **Don't create Vercel Postgres** (skip the Storage step)
2. **Manually set `DATABASE_URL`**:

```bash
vercel env add DATABASE_URL production
# Paste: postgresql://user:pass@host:5432/dbname?sslmode=require
```

## Testing Locally

To test with Vercel Postgres locally:

```bash
# Pull environment variables (includes POSTGRES_URL)
vercel env pull .env.local

# Run your application
python api/main.py
# or
vercel dev
```

The `.env.local` file will contain `POSTGRES_URL` and your app will use it automatically.

## Troubleshooting

### "No database connection"

- ✅ Check that Vercel Postgres database is created
- ✅ Verify environment variables exist in Vercel Dashboard
- ✅ Redeploy after creating database: `vercel deploy --prod`

### "Still using SQLite"

- ✅ Make sure you pulled environment variables: `vercel env pull .env.local`
- ✅ Check `.env.local` contains `POSTGRES_URL`
- ✅ Restart your local server

### "Connection refused"

- ✅ Verify database is in the same Vercel project
- ✅ Check database region matches your deployment region
- ✅ Ensure database is not paused (check Vercel Dashboard)

## Summary

| Scenario | What You Need |
|----------|---------------|
| **Vercel Postgres** | ✅ Nothing! Vercel auto-adds `POSTGRES_URL` |
| **Supabase/Neon/etc** | ✅ Manually set `DATABASE_URL` |
| **Local Development** | ✅ `vercel env pull .env.local` to get variables |

## Benefits of Vercel Postgres

- ✅ **Zero configuration** - No manual connection strings
- ✅ **Automatic backups** - Built-in backup system
- ✅ **Integrated** - Works seamlessly with Vercel deployments
- ✅ **Scaling** - Automatically scales with your usage
- ✅ **Free tier** - Generous free tier for small projects

---

**Note:** The application code automatically detects and uses Vercel's Postgres environment variables, so you don't need to change anything in your code!
