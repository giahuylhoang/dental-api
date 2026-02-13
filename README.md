# Dental API - FastAPI Service

FastAPI service for database and calendar operations, deployed on Vercel or other providers.

## Project Structure

```
dental-api/
├── api/                     # API-specific code
│   ├── main.py             # FastAPI app
│   ├── models.py           # Pydantic request/response models
│   └── routes/             # API route handlers (optional)
├── database/               # Database layer
│   ├── connection.py       # Database connection and session management
│   ├── models.py           # SQLAlchemy models
│   └── schema.py           # Database schema
├── services/               # Business logic
│   └── calendar_service.py # Wrapper around calendar_tools
├── tools/                  # Calendar integration tools
│   ├── calendar_tools.py
│   ├── doctor_calendars.py
│   └── event_template.py
├── scripts/                # Database scripts
│   ├── init_database.py
│   └── sync_db_calendar.py
├── app.py                  # Vercel entrypoint
├── vercel.json             # Vercel configuration
├── pyproject.toml
├── requirements.txt
├── Dockerfile
└── README.md
```

## Dependencies

- fastapi
- uvicorn
- sqlalchemy
- psycopg2-binary (PostgreSQL)
- google-api-python-client
- google-auth-oauthlib
- httpx
- pydantic
- pytz

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string (e.g., `postgresql://user:pass@host:5432/db`)

Google Calendar (choose one):
- `GOOGLE_SERVICE_ACCOUNT_JSON` - Service account JSON (recommended for production)
- OR `GOOGLE_TOKEN_JSON` + `GOOGLE_CREDENTIALS_JSON` - OAuth credentials (for development)

Optional:
- `CALENDAR_API_PORT` - API port (defaults to 8000)

## Setup

1. Copy `.env.example` to `.env` and fill in your configuration
2. Install dependencies: `uv sync` or `pip install -r requirements.txt`
3. Initialize database: `python scripts/init_database.py`
4. Run locally: `uvicorn api.main:app --reload`

## Deployment

### Vercel

Deploy to Vercel using the provided `vercel.json` and `app.py`:

```bash
vercel deploy
```

### Docker

Build and run with Docker:

```bash
docker build -t dental-api .
docker run -p 8000:8000 --env-file .env dental-api
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

### Health
- `GET /health` - Health check endpoint

## Database

The API uses SQLAlchemy with PostgreSQL (or SQLite for development). Database models are defined in `database/models.py`.

To initialize the database:
```bash
python scripts/init_database.py
```

To sync database with Google Calendar:
```bash
python scripts/sync_db_calendar.py
```
