# Initialize Database on Vercel

After deploying your FastAPI app to Vercel, you need to initialize the database (create tables and seed initial data).

## Method 1: Using Local Script (Recommended)

This method connects to your Vercel database from your local machine.

### Step 1: Pull Environment Variables from Vercel

```bash
cd dental-api

# Pull environment variables (creates .env.local)
vercel env pull .env.local
```

This downloads all your Vercel environment variables including `DATABASE_URL`.

### Step 2: Run Initialization Script

```bash
python scripts/init_vercel_db.py
```

This will:
- ✅ Connect to your Vercel PostgreSQL database
- ✅ Create all tables
- ✅ Seed initial data (doctors and services)

### Step 3: Verify

```bash
# Test API endpoint
curl https://your-app.vercel.app/api/doctors

# Should return list of doctors
```

## Method 2: Using API Endpoint (Alternative)

Add an initialization endpoint to your API (for one-time use only).

### Add to `api/main.py`:

```python
@app.post("/api/admin/init-db")
async def init_database_endpoint():
    """Initialize database schema (admin only - remove after first use)."""
    try:
        init_db()
        from scripts.init_vercel_db import seed_initial_data
        seed_initial_data()
        return {"message": "Database initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Then call it:

```bash
curl -X POST https://your-app.vercel.app/api/admin/init-db
```

⚠️ **Important:** Remove this endpoint after initialization for security!

## Method 3: Using Vercel CLI (Advanced)

You can also run commands directly on Vercel:

```bash
# This requires Vercel CLI and may have limitations
vercel exec -- python scripts/init_database.py
```

Note: This method may not work depending on your Vercel plan.

## Quick Start

```bash
# 1. Pull env vars
cd dental-api
vercel env pull .env.local

# 2. Initialize database
python scripts/init_vercel_db.py

# 3. Verify
curl https://your-app.vercel.app/api/doctors
```

## Troubleshooting

### Error: "DATABASE_URL not set"

**Solution:**
```bash
# Pull environment variables from Vercel
vercel env pull .env.local

# Verify it contains DATABASE_URL
cat .env.local | grep DATABASE_URL
```

### Error: "Connection refused" or "Could not connect"

**Possible causes:**
1. Database not accessible from your IP
2. Wrong connection string
3. Database not created in Vercel

**Solutions:**
- Check Vercel Dashboard → Storage → Your Database
- Verify `DATABASE_URL` in `.env.local`
- For Supabase: Check IP whitelist in Supabase dashboard

### Error: "relation already exists"

**Solution:** Tables already exist. This is fine if you just want to seed data:

```bash
# Skip table creation, just seed data
python -c "from scripts.init_vercel_db import seed_initial_data; seed_initial_data()"
```

### Tables Created But No Data

**Solution:** Run seed function separately:

```bash
python -c "
from scripts.init_vercel_db import seed_initial_data
seed_initial_data()
"
```

## Verify Database is Initialized

### Check Tables Exist

```bash
# Via API
curl https://your-app.vercel.app/api/doctors
curl https://your-app.vercel.app/api/services

# Should return data, not empty arrays
```

### Check Database Directly (Supabase)

1. Go to Supabase Dashboard
2. Table Editor
3. You should see:
   - `doctors` table (with 3 doctors)
   - `services` table (with 70 services)
   - `patients` table (empty, ready for data)
   - `appointments` table (empty, ready for data)
   - `leads` table (empty, ready for data)

## After Initialization

✅ Database tables created
✅ Initial data seeded (doctors and services)
✅ Ready to accept:
   - Patient records
   - Appointments
   - Leads

## Next Steps

1. ✅ Verify API endpoints work
2. ✅ Test creating a patient via API
3. ✅ Update agent `CALENDAR_API_URL` to point to Vercel
4. ✅ Deploy agent to LiveKit Cloud

## Security Note

⚠️ **Never expose initialization endpoints in production!**

If you add an `/api/admin/init-db` endpoint:
- Remove it after first use
- Add authentication/authorization
- Or use environment variable to disable it

## Example: Complete Initialization

```bash
# 1. Navigate to project
cd dental-api

# 2. Pull Vercel environment variables
vercel env pull .env.local

# 3. Verify DATABASE_URL is set
cat .env.local | grep DATABASE_URL

# 4. Initialize database
python scripts/init_vercel_db.py

# 5. Verify it worked
curl https://your-app.vercel.app/api/doctors
curl https://your-app.vercel.app/api/services

# Should see doctors and services data
```

Done! Your Vercel database is now initialized. 🎉
