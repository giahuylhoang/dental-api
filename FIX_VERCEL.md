# Fix Vercel Deployment Issue

## Problem

Vercel is serving `app.py` as a static file instead of executing it as a Python function.

## Solution

I've updated the configuration. You need to redeploy:

### Option 1: Quick Fix (Recommended)

1. **Update vercel.json** - Already done ✅
2. **Redeploy:**

```bash
cd dental-api
vercel deploy --prod
```

### Option 2: Alternative Configuration

If Option 1 doesn't work, try this `vercel.json`:

```json
{
  "buildCommand": "echo 'Build complete'",
  "outputDirectory": ".",
  "framework": null,
  "functions": {
    "api/index.py": {
      "runtime": "python3.11"
    }
  },
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/api"
    }
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
}
```

## What Changed

1. ✅ Created `api/index.py` - Vercel auto-detects Python files in `api/` directory
2. ✅ Updated `vercel.json` - Routes to `/api` instead of `/app.py`
3. ✅ Vercel will now execute Python code instead of serving it as static

## After Redeploy

```bash
# Test again
curl https://dental-api-ochre.vercel.app/health
curl https://dental-api-ochre.vercel.app/api/doctors
```

## If Still Not Working

Make sure:
1. ✅ `requirements.txt` exists (Vercel needs this to detect Python)
2. ✅ Python version is specified (3.11+)
3. ✅ All dependencies are in `requirements.txt`

Check Vercel Dashboard → Deployments → Your Deployment → Functions tab
- You should see `api/index.py` listed as a serverless function
