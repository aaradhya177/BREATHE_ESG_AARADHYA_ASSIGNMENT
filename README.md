# Breathe ESG — Emissions Ingestion & Analyst Review Tool

A Django REST + React prototype that ingests carbon emissions data from three enterprise source types, normalizes it into a unified model, and surfaces a review dashboard where analysts can approve or flag records before they are locked for audit.

**Live URL:** `[add after Render deployment]`  
**Stack:** Django 4.2 · Django REST Framework · PostgreSQL · React 18 · Vite · Tailwind CSS

---

## What It Does

Enterprise clients generate emissions data from disparate systems — SAP exports for fuel, utility portal CSVs for electricity, and Concur-style JSON exports for business travel. None of these arrive in a consistent shape. This tool:

1. Accepts file uploads for each source type
2. Parses and normalizes them into a single `EmissionRecord` table
3. Assigns GHG Protocol scope (1/2/3), activity type, and CO2e estimates using DEFRA 2023 emission factors
4. Flags suspicious rows automatically (zero quantities, missing flight distances, long billing periods)
5. Presents an analyst dashboard to review, approve, reject, or flag records
6. Maintains a full audit log of every review action with before/after state snapshots

---

## Data Sources

| Source | Format | Scope | Ingestion Mode |
|---|---|---|---|
| SAP Fuel Export | Semicolon-delimited CSV, German headers, European decimal format | Scope 1 | File upload |
| Utility Electricity | Portal CSV export, multi-meter, non-calendar billing periods | Scope 2 | File upload |
| Corporate Travel | Concur-style JSON, flights/hotels/car/rail | Scope 3 | File upload |

Sample data for all three sources is in `backend/sample_data/`.

---

## Project Structure

```
breathe-esg/
├── backend/
│   ├── breathe/          # Django project settings
│   ├── emissions/        # Core models: Client, DataSource, IngestionBatch, EmissionRecord, AuditLog
│   ├── ingestion/        # Parsers for SAP, utility, travel + ingestion API views
│   ├── ingestion_batches/
│   └── sample_data/      # sap_fuel_sample.csv, utility_electricity_sample.csv, travel_sample.json
├── frontend/
│   └── src/              # React pages: Home, Upload, Review, Record Detail
├── MODEL.md              # Data model decisions
├── DECISIONS.md          # Every ambiguity resolved and why
├── TRADEOFFS.md          # Three deliberate cuts with reasoning
├── SOURCES.md            # Real-world format research for each source
└── docker-compose.yml    # Local PostgreSQL
```

---

## Running Locally

**Prerequisites:** Python 3.11+, Node 18+, Docker Desktop

```bash
# 1. Clone
git clone https://github.com/aaradhya177/BREATHE_ESG_AARADHYA_ASSIGNMENT.git
cd BREATHE_ESG_AARADHYA_ASSIGNMENT

# 2. Start database
docker-compose up -d postgres

# 3. Backend
cd backend
cp .env.example .env
# Fill in SECRET_KEY in .env (see .env.example)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_client
python manage.py runserver

# 4. Frontend (new terminal)
cd frontend
echo "VITE_API_URL=http://localhost:8000" > .env
npm install
npm run dev
```

Open `http://localhost:5173`. Backend health check at `http://localhost:8000/api/health/`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health/` | Health check |
| POST | `/api/ingest/sap/` | Upload SAP fuel CSV |
| POST | `/api/ingest/utility/` | Upload utility electricity CSV |
| POST | `/api/ingest/travel/` | Upload travel JSON |
| GET | `/api/batches/?client_slug=acme-corp` | List ingestion batches |
| GET | `/api/records/?batch_id=X&status=PENDING_REVIEW` | List emission records |
| PATCH | `/api/records/{id}/review/` | Approve / Reject / Flag a record |
| GET | `/api/records/{id}/audit-log/` | Full audit history for a record |

---

## Documentation

- `MODEL.md` — data model design and every field decision
- `DECISIONS.md` — source format choices, scope assignments, PM questions
- `TRADEOFFS.md` — what was deliberately not built and why
- `SOURCES.md` — real-world format research for SAP, utility, and travel data

---

## Grading Criteria (per assignment)

- 35% data model quality → see `MODEL.md`
- 25% decision defense → see `DECISIONS.md`
- 20% source realism → see `SOURCES.md`
- 10% analyst UX → review dashboard at `/review`
- 10% what was cut → see `TRADEOFFS.md`
