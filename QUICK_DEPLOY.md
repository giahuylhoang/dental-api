# Quick Deploy Guide: Dental API to Vercel

## Prerequisites Checklist

- [ ] Vercel account created
- [ ] Vercel CLI installed: `npm i -g vercel`
- [ ] PostgreSQL database ready (connection string)
- [ ] Google Calendar API credentials ready
- [ ] **If migrating from SQLite:** See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)

## 5-Minute Deployment

### 1. Install & Login (1 min)

```bash
npm i -g vercel
vercel login
cd dental-api
```

### 2. Link Project (1 min)

```bash
vercel link
# Answer prompts:
# - Set up and deploy? Y
# - Link to existing? N
# - Project name: dental-api
# - Directory: ./
```

### 3. Migrate from SQLite (If Applicable) (2 min)

**If you have existing SQLite data:**
```bash
# Set PostgreSQL connection string
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Run migration
python scripts/migrate_sqlite_to_postgres.py
```

**If starting fresh:**
```bash
# Just initialize empty database
python scripts/init_database.py
```

### 4. Set Environment Variables (2 min)

**Via Vercel Dashboard (Recommended):**
1. Go to https://vercel.com/dashboard
2. Select your project → Settings → Environment Variables
3. Add these variables:

```
DATABASE_URL = postgresql://user:pass@host:5432/db?sslmode=require
GOOGLE_SERVICE_ACCOUNT_JSON = {"type": "service_account", ...}
```

**Via CLI:**
```bash
vercel env add DATABASE_URL production
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production
```

### 5. Deploy (1 min)

```bash
vercel deploy --prod
```

### 6. Initialize Database (If Not Migrated) (1 min)

**If you already migrated locally, skip this step.**

```bash
# Pull env vars
vercel env pull .env.local

# Initialize database (creates tables and seeds initial data)
python scripts/init_database.py
```

### 7. Verify

```bash
# Get your deployment URL from terminal output
# Example: https://dental-api-xyz.vercel.app

curl https://your-app.vercel.app/health
# Should return: {"status": "ok"}
```

## Done! 🎉

Your API is now deployed. Copy the deployment URL and use it as `CALENDAR_API_URL` in your agent project.

## Common Issues

**Database connection fails?**
- Check `DATABASE_URL` includes `?sslmode=require`
- Verify database allows connections from Vercel IPs

**Calendar API fails?**
- Verify service account email is shared with your Google Calendar
- Check `GOOGLE_SERVICE_ACCOUNT_JSON` is valid JSON (single-line)

**Import errors?**
- Ensure you're deploying from `dental-api/` directory
- Check `app.py` exists in root

## Next Steps

1. Test API endpoints
2. Update agent `CALENDAR_API_URL` to point to deployed API
3. Deploy agent to LiveKit Cloud

For detailed instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)
