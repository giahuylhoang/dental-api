# How to Test Google Service Account JSON

Complete guide to test if your `GOOGLE_SERVICE_ACCOUNT_JSON` is working correctly.

## Quick Test

Run the test script:

```bash
cd dental-api
source ../.venv/bin/activate  # Activate virtual environment
python test_google_service_account.py
```

## Step-by-Step Setup

### 1. Get Your Service Account JSON

If you haven't created it yet, follow [GOOGLE_SERVICE_ACCOUNT_SETUP.md](./GOOGLE_SERVICE_ACCOUNT_SETUP.md).

### 2. Set Environment Variable Locally

**Option A: Add to .env.local file (Recommended)**

```bash
cd dental-api

# Create or edit .env.local
nano .env.local
# or
code .env.local
```

Add your service account JSON as a single line:

```bash
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"your-project","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com",...}'
```

**Important:** The entire JSON must be on one line!

**Option B: Use helper script to format it**

If you have the JSON file downloaded:

```bash
# Put your service account JSON file in dental-api directory
# Name it: service-account.json (or service_account.json)

# Run the helper script
python scripts/prepare_vercel_env.py
```

This will output the correctly formatted environment variable.

**Option C: Export directly (temporary)**

```bash
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

### 3. Share Calendar with Service Account

**Critical Step:** The service account needs access to your calendar!

1. Open the JSON file and find the `client_email` field
2. Copy that email (looks like: `xxx@xxx.iam.gserviceaccount.com`)
3. Open [Google Calendar](https://calendar.google.com/)
4. Go to **Settings** → **Settings for my calendars**
5. Select your calendar
6. Scroll to **Share with specific people**
7. Click **Add people**
8. Paste the service account email
9. Set permission to **"Make changes to events"**
10. Click **Send**

### 4. Run the Test

```bash
cd dental-api
source ../.venv/bin/activate
python test_google_service_account.py
```

## Expected Output

**If everything works:**

```
============================================================
Google Service Account Test
============================================================

🔍 Checking GOOGLE_SERVICE_ACCOUNT_JSON configuration...

✅ GOOGLE_SERVICE_ACCOUNT_JSON found
✅ Valid JSON format
✅ All required fields present

📋 Service Account Info:
   Type: service_account
   Project ID: your-project-id
   Client Email: your-service-account@your-project.iam.gserviceaccount.com

🔍 Checking dependencies...

✅ google-auth installed
✅ google-api-python-client installed

🔍 Testing service account credentials...

✅ Service account credentials created successfully
✅ Google Calendar API service created

🔍 Testing Google Calendar access...

✅ Successfully accessed Google Calendar API
✅ Found 2 calendar(s)

📅 Available calendars:
   - My Calendar (primary)
     Access: owner

✅ All critical tests passed! Your Google Service Account is working correctly.
```

## Troubleshooting

### Error: "GOOGLE_SERVICE_ACCOUNT_JSON not found"

**Solution:**
- Make sure `.env.local` file exists in `dental-api/` directory
- Check the variable name is exactly `GOOGLE_SERVICE_ACCOUNT_JSON`
- Verify the JSON is on a single line
- Try exporting it directly: `export GOOGLE_SERVICE_ACCOUNT_JSON='...'`

### Error: "Invalid JSON format"

**Solution:**
- Make sure the entire JSON is on one line
- Escape quotes properly: Use single quotes around the JSON string
- Use the helper script: `python scripts/prepare_vercel_env.py`

**Example of correct format:**
```bash
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"test",...}'
```

**Wrong format:**
```bash
GOOGLE_SERVICE_ACCOUNT_JSON="{"type":"service_account"}"  # Quotes not escaped
```

### Error: "Calendar access denied" or "Forbidden"

**Solution:**
1. ✅ Share your calendar with the service account email
2. ✅ Give it "Make changes to events" permission
3. ✅ Wait a few minutes for permissions to propagate
4. ✅ Verify the service account email matches the one in JSON

**To find service account email:**
```bash
python3 -c "import os, json; print(json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '{}')).get('client_email', 'NOT SET'))"
```

### Error: "Insufficient authentication scopes"

**Solution:**
- Make sure Google Calendar API is enabled in Google Cloud Console
- Verify the service account has Calendar API access
- Check that scopes include: `https://www.googleapis.com/auth/calendar`

### Error: "Invalid credentials" or "Invalid grant"

**Solution:**
- Generate a new service account key from Google Cloud Console
- Delete the old key
- Download new JSON and update `GOOGLE_SERVICE_ACCOUNT_JSON`

## Testing for Vercel Deployment

If you've set `GOOGLE_SERVICE_ACCOUNT_JSON` in Vercel but want to test locally:

```bash
# Pull environment variables from Vercel
cd dental-api
vercel env pull .env.local

# Run test
source ../.venv/bin/activate
python test_google_service_account.py
```

## Alternative: Test via API

If your API is running, you can also test via HTTP:

```bash
# Start API server
cd dental-api
source ../.venv/bin/activate
python api/main.py

# In another terminal, test calendar endpoint
curl http://localhost:8000/api/calendar/validate
# or
curl http://localhost:8000/api/calendar/list
```

## Quick Checklist

- [ ] Service account JSON downloaded from Google Cloud Console
- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON` set in `.env.local` or environment
- [ ] JSON is valid and properly formatted (single line)
- [ ] Google Calendar API enabled in Google Cloud Console
- [ ] Calendar shared with service account email
- [ ] Service account has "Make changes to events" permission
- [ ] Test script runs successfully
- [ ] Can list calendars
- [ ] Can create events (optional test)

## Next Steps

Once the test passes:

1. ✅ Your service account is configured correctly
2. ✅ Your application can use Google Calendar API
3. ✅ You can deploy to Vercel with the same environment variable
4. ✅ Calendar operations will work in production

For deployment, make sure to set `GOOGLE_SERVICE_ACCOUNT_JSON` in Vercel Dashboard → Environment Variables.
