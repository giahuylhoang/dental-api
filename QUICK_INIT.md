# Quick Initialize Your Vercel Database

Your API is deployed! Now initialize the database:

## Step 1: Pull Environment Variables

```bash
cd dental-api
vercel env pull .env.local
```

## Step 2: Initialize Database

```bash
python scripts/init_vercel_db.py
```

## Step 3: Test Your API

```bash
# Health check
curl https://dental-api-ochre.vercel.app/health

# List doctors (should return 3 doctors)
curl https://dental-api-ochre.vercel.app/api/doctors

# List services (should return 70 services)
curl https://dental-api-ochre.vercel.app/api/services
```

## Your Production URL

**Use this in your agent:**
```
CALENDAR_API_URL=https://dental-api-ochre.vercel.app
```

## Complete Commands

```bash
# 1. Pull env vars
cd dental-api
vercel env pull .env.local

# 2. Initialize database
python scripts/init_vercel_db.py

# 3. Test endpoints
curl https://dental-api-ochre.vercel.app/api/doctors
curl https://dental-api-ochre.vercel.app/api/services
```

Done! 🎉
