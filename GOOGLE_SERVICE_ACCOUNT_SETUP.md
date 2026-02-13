# How to Get GOOGLE_SERVICE_ACCOUNT_JSON

This guide walks you through creating a Google Service Account and getting the JSON credentials for your dental receptionist application.

## Why Service Account?

Service accounts are recommended for production because:
- ✅ No user interaction required (no OAuth flow)
- ✅ Works in serverless environments (Vercel, etc.)
- ✅ More secure for automated systems
- ✅ Tokens don't expire (unlike OAuth tokens)

## Step-by-Step Guide

### Step 1: Go to Google Cloud Console

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Select your project (or create a new one)

### Step 2: Enable Google Calendar API

1. Go to **APIs & Services** → **Library**
2. Search for "Google Calendar API"
3. Click on it and click **Enable**

### Step 3: Create a Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Fill in the details:
   - **Service account name**: `dental-receptionist-calendar` (or any name you prefer)
   - **Service account ID**: Auto-generated (you can change it)
   - **Description**: "Service account for dental receptionist calendar integration"
4. Click **Create and Continue**

### Step 4: Grant Permissions (Optional)

You can skip this step for now - we'll grant permissions directly to the calendar later.

1. Click **Continue** (skip role assignment)
2. Click **Done**

### Step 5: Create and Download JSON Key

1. Find your newly created service account in the list
2. Click on it to open details
3. Go to the **Keys** tab
4. Click **Add Key** → **Create new key**
5. Select **JSON** as the key type
6. Click **Create**
7. The JSON file will automatically download to your computer

**⚠️ Important:** Keep this JSON file secure! It contains credentials that allow access to your calendar.

### Step 6: Share Calendar with Service Account

The service account needs access to your Google Calendar:

1. Open the downloaded JSON file
2. Find the `client_email` field (looks like: `dental-receptionist-calendar@your-project.iam.gserviceaccount.com`)
3. Copy this email address
4. Open [Google Calendar](https://calendar.google.com/)
5. Go to **Settings** → **Settings for my calendars**
6. Select the calendar you want to use
7. Scroll down to **Share with specific people**
8. Click **Add people**
9. Paste the service account email address
10. Set permission to **Make changes to events** (or **Make changes to events and manage sharing**)
11. Click **Send**

### Step 7: Get the JSON Content

1. Open the downloaded JSON file in a text editor
2. Copy the **entire contents** of the file
3. It should look like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "dental-receptionist-calendar@your-project.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

### Step 8: Set as Environment Variable

#### For Local Development (.env.local)

1. Create or edit `.env.local` in your project root
2. Add the JSON as a single line (remove all line breaks):

```bash
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"your-project-id",...}'
```

**Or use a helper script:**

```bash
# Convert JSON file to single-line format
python -c "import json; print('GOOGLE_SERVICE_ACCOUNT_JSON=' + repr(json.dumps(json.load(open('path/to/service-account-key.json')))))"
```

#### For Vercel Deployment

```bash
# Set environment variable in Vercel
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production

# When prompted, paste the entire JSON as a single line
# Example: {"type":"service_account","project_id":"...","private_key":"...",...}
```

**Or use the helper script:**

```bash
python scripts/prepare_vercel_env.py
```

This will format the JSON correctly for Vercel.

## Verify Setup

Test that your service account works:

```bash
# Test locally
python -c "from tools.calendar_tools import validate_calendar_credentials; valid, msg = validate_calendar_credentials(); print('✅ Valid' if valid else f'❌ Error: {msg}')"
```

Or test in your application:

```python
from tools.calendar_tools import get_calendar_service

service = get_calendar_service()
calendars = service.calendarList().list().execute()
print(f"✅ Connected! Found {len(calendars.get('items', []))} calendars")
```

## Troubleshooting

### "Permission denied" or "Calendar not found"

- Make sure you shared the calendar with the service account email
- Check that the service account email matches the one in your JSON file
- Verify calendar sharing permissions are set correctly

### "Invalid credentials"

- Make sure the JSON is valid (no extra characters, proper escaping)
- For Vercel, ensure it's a single-line JSON string
- Check that you copied the entire JSON file contents

### "API not enabled"

- Go back to Google Cloud Console
- Enable Google Calendar API (Step 2 above)

### "Service account not found"

- Verify the JSON file is from the correct Google Cloud project
- Make sure the service account wasn't deleted

## Security Best Practices

1. **Never commit the JSON file to git**
   - Add `*.json` (or specific filename) to `.gitignore`
   - Use environment variables instead

2. **Rotate keys periodically**
   - Delete old keys in Google Cloud Console
   - Create new keys and update environment variables

3. **Limit calendar permissions**
   - Only share calendars that need to be accessed
   - Use "Make changes to events" instead of full access when possible

4. **Use different service accounts for different environments**
   - Separate service accounts for development, staging, and production

## Alternative: OAuth Credentials (For Development)

If you prefer OAuth for local development:

1. See [CALENDAR_REAUTH_GUIDE.md](../md_tmp/CALENDAR_REAUTH_GUIDE.md)
2. Use `GOOGLE_CREDENTIALS_JSON` and `GOOGLE_TOKEN_JSON` instead

## Next Steps

Once you have `GOOGLE_SERVICE_ACCOUNT_JSON` set:

1. ✅ Test the connection locally
2. ✅ Deploy to Vercel with the environment variable
3. ✅ Verify calendar operations work in production

For deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).
