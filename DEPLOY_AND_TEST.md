# Deploy to Vercel and Test

## 1. Log in to Vercel (if needed)

```bash
vercel login
```

If you see "The specified token is not valid", run the above and complete the browser login.

## 2. Deploy

From the project root:

```bash
cd /Users/giahuyhoangle/Projects/dental-api
vercel deploy --prod --yes
```

Or without `--yes` to answer prompts:

```bash
vercel deploy --prod
```

Copy the **production URL** from the output (e.g. `https://dental-api-xxx.vercel.app`).

## 3. Environment variables (first-time or if missing)

In [Vercel Dashboard](https://vercel.com/dashboard) → your project → **Settings** → **Environment Variables**, add:

| Name | Description |
|------|-------------|
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://...?sslmode=require` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service account JSON (single line) for Google Calendar |

Redeploy after changing env vars: **Deployments** → ⋮ → **Redeploy**.

## 4. Initialize database (first deploy only)

If the database is empty:

```bash
vercel env pull .env.local
python scripts/init_database.py
```

## 5. Test the deployment

Replace `YOUR_DEPLOY_URL` with the URL from step 2:

```bash
./test_vercel_api.sh https://YOUR_DEPLOY_URL
```

Or test health only:

```bash
curl https://YOUR_DEPLOY_URL/health
```

Expected: `{"status":"ok"}` (or similar).

## If you hit the 250 MB serverless limit

This project uses heavy Python deps (Google API client, SQLAlchemy, etc.). The unpacked bundle can exceed Vercel’s 250 MB limit. If deploy fails with “Serverless Function has exceeded the unzipped maximum size of 250 MB”:

- **Railway / Render / Fly.io** work well for this stack. Example (Railway): connect the repo, set `DATABASE_URL` and `GOOGLE_SERVICE_ACCOUNT_JSON`, and use start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
- **Vercel**: You can try enabling **Build Cache** in the project and redeploy, or remove optional deps and redeploy; if the bundle is still too large, use one of the platforms above.

## Quick reference

| Step        | Command |
|------------|---------|
| Login      | `vercel login` |
| Deploy     | `vercel deploy --prod --yes` |
| Test all   | `./test_vercel_api.sh <URL>` |
| Test health| `curl <URL>/health` |
