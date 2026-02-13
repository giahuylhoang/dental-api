# Deploying Dental API to Vercel

Step-by-step guide to deploy the dental-api project to Vercel.

## Prerequisites

- Vercel account ([sign up](https://vercel.com))
- Vercel CLI installed: `npm i -g vercel`
- PostgreSQL database (Vercel Postgres, Supabase, Neon, or external)
- Google Cloud project with Calendar API enabled

## Quick Start

### Step 1: Install Vercel CLI

```bash
npm i -g vercel
```

### Step 2: Navigate to Project

```bash
cd dental-api
```

### Step 3: Login to Vercel

```bash
vercel login
```

### Step 4: Link Project (First Time)

```bash
vercel link
# Follow prompts:
# - Set up and deploy? Y
# - Which scope? (select your account/team)
# - Link to existing project? N (for first deployment)
# - Project name? dental-api (or your preferred name)
# - Directory? ./
```

### Step 5: Set Environment Variables

Set these in Vercel Dashboard → Settings → Environment Variables, or via CLI:

#### Required: Database

> **Why DATABASE_URL?** Your database is NOT included in deployment. Vercel only deploys your code. The database runs on a separate PostgreSQL server. `DATABASE_URL` tells your app WHERE to find that database. See [WHY_DATABASE_URL.md](./WHY_DATABASE_URL.md) for details.

```bash
# Via CLI
vercel env add DATABASE_URL production
# Paste: postgresql://user:password@host:5432/dbname?sslmode=require
```

**Using Vercel Postgres (Recommended):**
1. Vercel Dashboard → Storage → Create Database → Postgres
2. Copy the connection string (automatically created)
3. Add as `DATABASE_URL` environment variable
   - Note: Vercel may auto-add this, but verify it's set

**Using External PostgreSQL (Supabase, Neon, Railway, etc.):**
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
```

**Important:** SQLite (`dental_clinic.db`) works locally but **will NOT work** on Vercel because:
- Vercel Functions have a read-only file system
- Functions are ephemeral (no persistent storage)
- You need a persistent PostgreSQL database service

#### Required: Google Calendar (Choose One Method)

**Option A: Service Account (Recommended for Production)**

```bash
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production
# Paste the entire JSON as a single-line string:
# {"type": "service_account", "project_id": "...", ...}
```

**How to get Service Account JSON:**
1. Google Cloud Console → IAM & Admin → Service Accounts
2. Create new service account
3. Grant "Calendar API" permissions
4. Create key → JSON → Download
5. Share your Google Calendar with the service account email
6. Copy entire JSON content and paste as environment variable

**Option B: OAuth Credentials (For Development)**

```bash
vercel env add GOOGLE_CREDENTIALS_JSON production
# Paste: {"installed": {"client_id": "...", "client_secret": "...", ...}}

vercel env add GOOGLE_TOKEN_JSON production
# Paste: {"token": "...", "refresh_token": "...", ...}
```

**How to get OAuth credentials:**
1. Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID → Desktop app
3. Download credentials.json
4. Run OAuth flow locally: `python scripts/reauthenticate_calendar.py`
5. Copy token.json content
6. Convert both to single-line JSON strings

#### Optional: API Port

```bash
vercel env add CALENDAR_API_PORT production
# Default: 8000
```

### Step 6: Deploy

```bash
# Preview deployment
vercel deploy

# Production deployment
vercel deploy --prod
```

### Step 7: Initialize Database

After deployment, initialize the database schema:

**Option A: Via Local Script (Recommended)**

```bash
# Pull environment variables locally
vercel env pull .env.local

# Run initialization script
python scripts/init_database.py
```

**Option B: Via Direct Database Connection**

Connect to your PostgreSQL database and run:

```sql
-- The init_database.py script will create tables automatically
-- But you can verify with:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

**Option C: Create Init Endpoint (Optional)**

Add this to `api/main.py` if you want to initialize via API:

```python
@app.post("/api/admin/init-db")
async def init_database_endpoint():
    """Initialize database schema (admin only)."""
    init_db()
    return {"message": "Database initialized"}
```

Then call:
```bash
curl -X POST https://your-app.vercel.app/api/admin/init-db
```

### Step 8: Verify Deployment

```bash
# Health check
curl https://your-app.vercel.app/health

# Expected response:
# {"status": "ok"}

# Calendar validation
curl https://your-app.vercel.app/api/admin/calendar/validate

# List doctors
curl https://your-app.vercel.app/api/doctors
```

## Project Structure

```
dental-api/
├── api/
│   └── main.py              # FastAPI application
├── database/
│   ├── connection.py        # Database connection
│   ├── models.py            # SQLAlchemy models
│   └── schema.py            # Database schema
├── tools/
│   ├── calendar_tools.py    # Google Calendar integration
│   ├── doctor_calendars.py
│   └── event_template.py
├── scripts/
│   ├── init_database.py      # Database initialization
│   └── sync_db_calendar.py  # Calendar sync
├── app.py                   # Vercel entrypoint
├── vercel.json              # Vercel configuration
├── pyproject.toml           # Python dependencies
└── requirements.txt          # Python dependencies (for pip)
```

## Configuration Files

### app.py (Vercel Entrypoint)

```python
from api.main import app
__all__ = ["app"]
```

### vercel.json

```json
{
  "buildCommand": "echo 'Build complete'",
  "outputDirectory": ".",
  "framework": null,
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/app.py"
    }
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
}
```

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅ Yes* | Service account JSON (recommended) |
| `GOOGLE_CREDENTIALS_JSON` | ✅ Yes* | OAuth credentials JSON (alternative) |
| `GOOGLE_TOKEN_JSON` | ✅ Yes* | OAuth token JSON (alternative) |
| `CALENDAR_API_PORT` | ❌ No | API port (default: 8000) |

*Choose either Service Account OR OAuth credentials

## Local Development Setup

Before deploying, test locally:

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
# Or using uv:
uv sync

# 3. Create .env file
cp .env.example .env
# Edit .env with your local values

# 4. Initialize database
python scripts/init_database.py

# 5. Run locally
uvicorn api.main:app --reload
# Or using Vercel dev:
vercel dev
```

## Continuous Deployment

### Connect Git Repository

1. Vercel Dashboard → Add New Project
2. Import Git Repository (GitHub/GitLab/Bitbucket)
3. Configure:
   - **Framework Preset:** Other
   - **Root Directory:** `dental-api`
   - **Build Command:** (leave empty or `echo 'Build complete'`)
   - **Output Directory:** `.`
   - **Install Command:** `pip install -r requirements.txt` or `uv sync`

4. Add environment variables in dashboard
5. Deploy automatically on push

### Manual Deployment

```bash
# Preview
vercel deploy

# Production
vercel deploy --prod
```

## Troubleshooting

### Build Fails

```bash
# Check build logs
vercel logs

# Test locally first
vercel dev
```

### Database Connection Issues

```bash
# Verify DATABASE_URL format
vercel env ls

# Test connection locally
python -c "from database.connection import engine; engine.connect()"
```

**Common Issues:**
- Missing `?sslmode=require` for external databases
- Database not accessible from Vercel IPs
- Wrong credentials

### Calendar Token Issues

```bash
# Validate calendar credentials
curl https://your-app.vercel.app/api/admin/calendar/validate

# Refresh token (if using OAuth)
curl -X POST https://your-app.vercel.app/api/admin/calendar/refresh
```

**Common Issues:**
- Service account email not shared with calendar
- OAuth token expired (needs refresh)
- JSON format incorrect (must be single-line)

### Import Errors

If you see import errors like `ModuleNotFoundError: No module named 'api'`:

1. Ensure `app.py` is in the root of `dental-api/`
2. Check `vercel.json` rewrites are correct
3. Verify Python version (3.11+)

### Function Timeout

Vercel Functions have execution limits:
- **Hobby:** 10 seconds
- **Pro:** 60 seconds
- **Enterprise:** 300 seconds

**Solutions:**
- Optimize database queries
- Use async/await properly
- Consider breaking into smaller endpoints
- Upgrade to Pro plan

## Monitoring

### Vercel Dashboard

- View function logs
- Monitor performance metrics
- Check error rates
- View deployment history

### Health Checks

```bash
# API health
curl https://your-app.vercel.app/health

# Calendar validation
curl https://your-app.vercel.app/api/admin/calendar/validate

# List appointments
curl https://your-app.vercel.app/api/appointments
```

## Security Best Practices

1. **Never commit secrets:**
   - Use `.vercelignore` for sensitive files
   - Store all secrets in Vercel environment variables

2. **Use HTTPS:**
   - Vercel provides SSL automatically
   - All requests are HTTPS by default

3. **API Authentication (Recommended):**
   - Add API key authentication middleware
   - Use Vercel's built-in authentication
   - Implement rate limiting

4. **Database Security:**
   - Use SSL connections (`?sslmode=require`)
   - Restrict database access to Vercel IPs
   - Use connection pooling
   - Never expose database credentials

## Cost Considerations

- **Vercel Hobby Plan:** Free (with limits)
- **Vercel Pro Plan:** $20/month (better limits)
- **Database:** Vercel Postgres or external (varies)
- **Bandwidth:** Included in plan

## Next Steps After Deployment

1. ✅ Verify API is accessible
2. ✅ Initialize database
3. ✅ Test calendar integration
4. ✅ Update agent `CALENDAR_API_URL` to point to deployed API
5. ✅ Set up monitoring and alerts
6. ✅ Configure custom domain (optional)
7. ✅ Set up CI/CD pipeline

## Example: Complete First Deployment

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Navigate to project
cd dental-api

# 3. Login
vercel login

# 4. Link project
vercel link

# 5. Set database URL
vercel env add DATABASE_URL production
# Paste: postgresql://user:pass@host:5432/db?sslmode=require

# 6. Set Google Calendar credentials
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production
# Paste: {"type": "service_account", ...}

# 7. Deploy
vercel deploy --prod

# 8. Get deployment URL
# Copy from terminal output or Vercel dashboard

# 9. Pull env vars locally
vercel env pull .env.local

# 10. Initialize database
python scripts/init_database.py

# 11. Verify
curl https://your-app.vercel.app/health
```

## Resources

- [Vercel FastAPI Documentation](https://vercel.com/docs/frameworks/fastapi)
- [Vercel Functions Documentation](https://vercel.com/docs/functions)
- [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Calendar API](https://developers.google.com/calendar)
