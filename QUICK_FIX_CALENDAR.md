# Quick Fix: Calendar Service Not Working in Vercel

## Problem
- ✅ Calendar validation endpoint works (`/api/admin/calendar/validate` returns valid)
- ❌ Calendar service fails (`/api/calendar/slots` returns "No valid credentials found")

## Root Cause
`GOOGLE_SERVICE_ACCOUNT_JSON` is **NOT set in Vercel production environment**, even though it's set locally.

## Solution

### Option 1: Use Helper Script (Easiest)

```bash
cd dental-api
chmod +x add_to_vercel.sh
./add_to_vercel.sh
```

This will:
1. Read `GOOGLE_SERVICE_ACCOUNT_JSON` from `.env.local`
2. Add it to Vercel production environment
3. Show you next steps

### Option 2: Manual Steps

1. **Get your service account JSON** (already in `.env.local`):
   ```bash
   cd dental-api
   python3 get_service_account_email.py
   # This shows the email, but you need the full JSON
   ```

2. **Copy the JSON value** from `.env.local`:
   ```bash
   grep GOOGLE_SERVICE_ACCOUNT_JSON dental-api/.env.local
   ```

3. **Add to Vercel Dashboard**:
   - Go to: https://vercel.com/dashboard
   - Select project: **dental-api-ochre**
   - Go to **Settings** → **Environment Variables**
   - Click **Add New**
   - Name: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - Value: Paste the entire JSON (single line)
   - Environment: Select **Production** (and optionally Preview)
   - Click **Save**

4. **Or use Vercel CLI**:
   ```bash
   cd dental-api
   vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production
   # When prompted, paste the JSON value
   ```

### Option 3: Pull from Local and Push to Vercel

```bash
cd dental-api

# Get the JSON value
SA_JSON=$(grep "^GOOGLE_SERVICE_ACCOUNT_JSON=" .env.local | cut -d'=' -f2- | sed "s/^'//" | sed "s/'$//")

# Add to Vercel
echo "$SA_JSON" | vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production
```

## After Adding

1. **Redeploy** (Vercel will auto-deploy, or manually):
   ```bash
   cd dental-api
   vercel deploy --prod
   ```

2. **Wait 1-2 minutes** for deployment to complete

3. **Test**:
   ```bash
   # Should return valid
   curl https://dental-api-ochre.vercel.app/api/admin/calendar/validate
   
   # Should now work (not return "No valid credentials")
   curl "https://dental-api-ochre.vercel.app/api/calendar/slots?start_datetime=2025-12-27T09:00:00&end_datetime=2025-12-27T17:00:00"
   ```

## Verify It's Set

Check if it's now in Vercel:

```bash
cd dental-api
vercel env pull .env.vercel
grep GOOGLE_SERVICE_ACCOUNT_JSON .env.vercel
```

If you see the variable, it's set! 🎉

## Important Notes

- The JSON must be a **single line** (no line breaks)
- Make sure to select **Production** environment
- You may also want to add it to **Preview** environment for testing
- After adding, Vercel will automatically redeploy, or you can trigger a manual deploy

## Still Not Working?

1. **Check Vercel logs**:
   - Vercel Dashboard → Your Project → Deployments → Click latest → View Function Logs
   - Look for errors related to `GOOGLE_SERVICE_ACCOUNT_JSON`

2. **Verify JSON format**:
   ```bash
   # Test locally first
   python3 -c "import os, json; from dotenv import load_dotenv; load_dotenv('dental-api/.env.local'); sa = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')); print('Valid!')"
   ```

3. **Check service account email**:
   ```bash
   python3 dental-api/get_service_account_email.py
   ```
   Make sure you've shared your calendar with this email!
