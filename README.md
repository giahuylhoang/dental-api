# Dental API - FastAPI Service

FastAPI service for database and calendar operations. Primary deployment target: Google Cloud Run (see [DEPLOY_GOOGLE_CLOUD.md](DEPLOY_GOOGLE_CLOUD.md)).

Archived files (tests, frontend, extra scripts, other platforms) live under `tmp/`. See [tmp/README.md](tmp/README.md) for structure.

## Project Structure

```
dental-api/
├── api/
│   └── main.py             # FastAPI app
├── database/
│   ├── connection.py       # Database connection and session management
│   └── models.py           # SQLAlchemy models
├── tools/
│   └── slot_utils.py       # Calendar slot logic
├── scripts/
│   ├── sync_db.py          # Initialize schema and seed data
│   ├── init_database.py    # Seed logic (doctors, services)
│   ├── service_descriptions.py
│   └── migrate_add_clinics.py
├── run_api.py              # Container entrypoint
├── pyproject.toml
├── requirements.txt
├── Dockerfile
└── README.md
```

## Multi-clinic (multi-tenant)

The API supports multiple clinics with a single deployment. All data is scoped by clinic.

- **Tenant identification:** Send `X-Clinic-Id: clinic-id` on each request. Omit it (or use `"default"`) to use the default clinic.
- **Per-clinic config:** Each clinic has its own timezone, working hours, and name in the `clinics` table.
- **Frontend:** Build with `VITE_CLINIC_ID=clinic-a` so the frontend sends `X-Clinic-Id: clinic-a` on all API calls.

## Dependencies

- fastapi
- uvicorn
- sqlalchemy
- psycopg2-binary (PostgreSQL)
- pydantic
- httpx
- pytz
- python-dotenv

## Environment Variables

Required for API:
- `DATABASE_URL` - PostgreSQL connection string (or SQLite `sqlite:///./dental_clinic.db` for local dev)

Optional for frontend builds (`tmp/dental-calendar/`):
- `VITE_API_URL` - API base URL (default: `http://localhost:8000`)
- `VITE_CLINIC_ID` - Clinic ID sent as `X-Clinic-Id` (default: `"default"`)

## Setup

1. Install dependencies: `uv sync` or `pip install -r requirements.txt`
2. Initialize database: `DATABASE_URL=sqlite:///./dental_clinic.db python scripts/sync_db.py`
3. Run locally: `uvicorn api.main:app --reload --port 8001`

API requests default to clinic `"default"` unless you send `X-Clinic-Id`.

## Deployment

Primary target: **Google Cloud Run** — see [DEPLOY_GOOGLE_CLOUD.md](DEPLOY_GOOGLE_CLOUD.md) for full DB + app deployment and multi-clinic setup.

Docker:

```bash
docker build -t dental-api .
docker run -p 8000:8000 -e DATABASE_URL=postgresql://... dental-api
```

## API Endpoints

### Calendar
- `GET /api/calendar/slots` - Get available calendar slots
- `POST /api/calendar/events` - Create calendar event

### Appointments
- `GET /api/appointments` - List/search appointments
- `GET /api/appointments/{id}` - Get appointment by ID
- `POST /api/appointments` - Create appointment
- `PUT /api/appointments/{id}` - Update appointment
- `PUT /api/appointments/{id}/cancel` - Cancel appointment
- `PUT /api/appointments/{id}/reschedule` - Reschedule appointment
- `PUT /api/appointments/{id}/status` - Update appointment status
- `DELETE /api/appointments/{id}` - Delete appointment

### Patients
- `GET /api/patients` - List/search patients
- `GET /api/patients/{id}` - Get patient by ID
- `POST /api/patients` - Create patient
- `POST /api/patients/verify` - Verify patient identity
- `PUT /api/patients/{id}` - Update patient

### Doctors
- `GET /api/doctors` - List doctors
- `GET /api/doctors/{id}` - Get doctor by ID

### Services
- `GET /api/services` - List services
- `GET /api/services/{id}` - Get service by ID

### Leads
- `GET /api/leads` - List leads
- `GET /api/leads/{id}` - Get lead by ID
- `POST /api/leads` - Create lead
- `PUT /api/leads/{id}` - Update lead
- `PUT /api/leads/{id}/status` - Update lead status

### Clinics
- `POST /api/clinics` - Create clinic
- `GET /api/clinics/me` - Get current clinic config (from `X-Clinic-Id` header)

### Health
- `GET /health` - Health check endpoint

## Database

The API uses SQLAlchemy with PostgreSQL (Cloud Run) or SQLite (local dev). Models are in `database/models.py`.

Initialize schema and seed data:
```bash
DATABASE_URL=postgresql://... python scripts/sync_db.py
```

For existing DBs adding multi-clinic support:
```bash
DATABASE_URL=postgresql://... python scripts/migrate_add_clinics.py
```
