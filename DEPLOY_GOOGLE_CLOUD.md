# Deploy Dental API to Google Cloud Run

This guide covers deploying the Dental API to Google Cloud Run.

## Prerequisites

- Google Cloud SDK (`gcloud`) installed
- Project with billing enabled
- Artifact Registry API enabled

---

## Complete deployment (DB + App)

Use this section to deploy both Cloud SQL (PostgreSQL) and the API from scratch.

### Phase 1: Enable APIs and create Cloud SQL

```bash
gcloud config set project YOUR_PROJECT_ID

gcloud services enable sqladmin.googleapis.com run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# Create Cloud SQL instance
gcloud sql instances create dental-api-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Set root password
gcloud sql users set-password postgres --instance=dental-api-db --password=YOUR_SECURE_PASSWORD

# Create database and app user
gcloud sql databases create dental_clinic --instance=dental-api-db
gcloud sql users create dentalapp --instance=dental-api-db --password=YOUR_APP_PASSWORD

# Get connection name
gcloud sql instances describe dental-api-db --format="value(connectionName)"
# Output: PROJECT_ID:us-central1:dental-api-db
```

### Phase 2: Build and deploy API

```bash
# Create Artifact Registry repo
gcloud artifacts repositories create dental-api --repository-format=docker --location=us-central1

# Build and push (Cloud Build, no local Docker needed)
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/dental-api/dental-api:latest .

# Deploy to Cloud Run
CONNECTION_NAME="YOUR_PROJECT_ID:us-central1:dental-api-db"
gcloud run deploy dental-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/dental-api/dental-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances=$CONNECTION_NAME \
  --set-env-vars "DATABASE_URL=postgresql://dentalapp:YOUR_APP_PASSWORD@/dental_clinic?host=/cloudsql/$CONNECTION_NAME" \
  --set-env-vars "WORKING_HOUR_START=9" \
  --set-env-vars "WORKING_HOUR_END=17"
```

**DATABASE_URL format for Cloud Run:** Cloud Run uses a Unix socket. The URL must be:

```
postgresql://USER:PASSWORD@/DB_NAME?host=/cloudsql/CONNECTION_NAME
```

Replace `CONNECTION_NAME` with `PROJECT_ID:REGION:INSTANCE_NAME`.

### Phase 3: Initialize database (sync_db)

Cloud Run uses a Unix socket that is not reachable from your machine. Use one of these:

**Option A: Cloud SQL Auth Proxy** (recommended)

1. [Install Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy#install)
2. Run: `cloud-sql-proxy YOUR_PROJECT_ID:us-central1:dental-api-db --port=5432`
3. In another terminal:

```bash
DATABASE_URL="postgresql://dentalapp:YOUR_APP_PASSWORD@127.0.0.1:5432/dental_clinic" python scripts/sync_db.py
```

**Option B: Cloud Shell**

1. Open [Cloud Shell](https://console.cloud.google.com)
2. Clone the repo or upload `scripts/`, `database/`, `tools/`, `api/`
3. Run sync via Auth Proxy in Cloud Shell, or add Cloud Shell IP to Cloud SQL authorized networks and use TCP `DATABASE_URL`

### Phase 4: Verify

```bash
gcloud run services describe dental-api --region us-central1 --format="value(status.url)"
curl https://YOUR-URL/health
curl -H "X-Clinic-Id: default" https://YOUR-URL/api/doctors
```

---

## Environment Variables

Set these when deploying:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `PORT` | Port for the container (default 8000, set by Cloud Run) |
| `WORKING_HOUR_START` | Default working hour start (legacy; prefer per-clinic config in `clinics` table) |
| `WORKING_HOUR_END` | Default working hour end (legacy; prefer per-clinic config in `clinics` table) |

## Multi-clinic (multi-tenant)

The API is multi-tenant. Each request is scoped by `X-Clinic-Id` (default: `"default"`). Per-clinic config (timezone, working hours) is stored in the `clinics` table. For a fresh DB, `scripts/sync_db.py` creates the default clinic. For existing DBs, run:

```bash
DATABASE_URL=postgresql://... python scripts/migrate_add_clinics.py
```

## Steps

### 1. Configure Google Cloud

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 2. Create Artifact Registry repository

```bash
gcloud artifacts repositories create dental-api \
  --repository-format=docker \
  --location=us-central1
```

### 3. Build and push Docker image

```bash
# Build
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/dental-api/dental-api:latest .

# Authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/dental-api/dental-api:latest
```

### 4. Deploy to Cloud Run

```bash
gcloud run deploy dental-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/dental-api/dental-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql://..." \
  --set-env-vars "WORKING_HOUR_START=9" \
  --set-env-vars "WORKING_HOUR_END=17"
```

Or use a secret for `DATABASE_URL`:

```bash
# Create secret first
echo -n "postgresql://user:pass@host:5432/db" | gcloud secrets create db-url --data-file=-

# Deploy with secret
gcloud run deploy dental-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/dental-api/dental-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets "DATABASE_URL=db-url:latest"
```

### 5. Initialize database

After first deploy, run the sync script against your database (from a machine with DB access):

```bash
DATABASE_URL=postgresql://... python scripts/sync_db.py
```

## Frontend

The React calendar frontend (`dental-calendar/` or `tmp/dental-calendar/`) is a separate app. Deploy it to:

- Firebase Hosting
- Cloud Storage + Load Balancer
- Or any static hosting

Set `VITE_API_URL` to your Cloud Run URL and `VITE_CLINIC_ID` for the clinic (default: `"default"`) when building:

```bash
cd dental-calendar
VITE_API_URL=https://your-service-xxx.run.app VITE_CLINIC_ID=default npm run build
```

Per-clinic deployments: use `VITE_CLINIC_ID=clinic-a` so the frontend sends `X-Clinic-Id: clinic-a` on all API requests.
