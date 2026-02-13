# Deploy dental-api on Railway

## 1. Create a Railway project

1. Go to [railway.app](https://railway.app) and sign in (GitHub is easiest).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your `dental-api` repo (or the one that contains this code).
4. Railway will detect Python and use the **Procfile** (or **Dockerfile** if you choose that builder).

## 2. Set environment variables

In the Railway project: **Variables** (or **Settings** → **Variables**), add:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:pass@host:5432/db?sslmode=require` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full Google service account JSON (single line) for Calendar API |

Optional:

- `CALENDAR_API_PORT` – usually not needed; Railway sets `PORT`.

## 3. Deploy

- If you chose **Deploy from GitHub**, every push to the linked branch triggers a deploy.
- Or use the **Railway CLI**: `railway up` from the project root (after `railway link`).

## 4. Get the URL and test

- In the dashboard, open your service → **Settings** → **Networking** → **Generate domain** (or use the default `.railway.app` URL).
- Test:

```bash
curl https://YOUR-APP.up.railway.app/health
```

Expected: `{"status":"ok"}` or similar.

## 5. Initialize the database (first time)

If the database is empty, run the init script once (from your machine with env vars, or via Railway’s shell):

```bash
# Option A: use Railway CLI and run locally with Railway env
railway run python scripts/init_database.py

# Option B: set DATABASE_URL in Railway, then run the same command in a one-off shell
```

## Build options

- **Nixpacks (default)** – Railway uses the **Procfile** and installs deps from `requirements.txt`. No Docker needed.
- **Dockerfile** – In the service **Settings** → **Build**, you can choose **Dockerfile** so Railway builds and runs the **Dockerfile** in this repo (uses `$PORT` automatically).

## Quick reference

| Step | Action |
|------|--------|
| New project | Railway → New Project → Deploy from GitHub → select repo |
| Env vars | Variables → add `DATABASE_URL`, `GOOGLE_SERVICE_ACCOUNT_JSON` |
| URL | Settings → Networking → Generate domain |
| Health check | `curl https://YOUR-APP.up.railway.app/health` |
