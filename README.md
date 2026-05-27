# Breathe ESG - Emissions Ingestion & Analyst Review Tool

A Django REST + React prototype that ingests carbon emissions data from three enterprise source types, normalizes it into a unified model, and surfaces a review dashboard where analysts can approve or flag records before audit.

**Live URL:** https://breathe-esg-aaradhya-assignment.vercel.app/
**Stack:** Django 4.2, Django REST Framework, PostgreSQL, React 18, Vite, Tailwind CSS

## What It Does

Enterprise clients generate emissions data from disparate systems: SAP exports for fuel, utility portal CSVs for electricity, and Concur-style JSON exports for business travel. None of these arrive in a consistent shape. This tool:

1. Accepts file uploads for each source type
2. Parses and normalizes them into a single `EmissionRecord` table
3. Assigns GHG Protocol scope 1/2/3, activity type, and CO2e estimates using DEFRA 2023 emission factors
4. Flags suspicious rows automatically, such as zero quantities, missing flight distances, and long billing periods
5. Presents an analyst dashboard to review, approve, reject, or flag records
6. Maintains a full audit log of every review action with before/after state snapshots

## Data Sources

| Source | Format | Scope | Ingestion Mode |
|---|---|---|---|
| SAP Fuel Export | Semicolon-delimited CSV, German headers, European decimal format | Scope 1 | File upload |
| Utility Electricity | Portal CSV export, multi-meter, non-calendar billing periods | Scope 2 | File upload |
| Corporate Travel | Concur-style JSON, flights/hotels/car/rail | Scope 3 | File upload |

Sample data for all three sources is in `backend/sample_data/`.

## Project Structure

```text
breathe-esg/
  backend/
    breathe/          # Django project settings
    emissions/        # Core models
    ingestion/        # Parsers and API views
    sample_data/      # Sample SAP, utility, and travel files
  frontend/
    src/              # React pages and API client
  MODEL.md
  DECISIONS.md
  TRADEOFFS.md
  SOURCES.md
  docker-compose.yml
  render.yaml
```

## Running Locally

Prerequisites: Python 3.11+, Node 18+, Docker Desktop.

```bash
git clone https://github.com/aaradhya177/BREATHE_ESG_AARADHYA_ASSIGNMENT.git
cd BREATHE_ESG_AARADHYA_ASSIGNMENT

docker-compose up -d postgres

cd backend
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_client
python manage.py runserver
```

In a second terminal:

```bash
cd frontend
echo "VITE_API_URL=http://localhost:8000" > .env
npm install
npm run dev
```

Open `http://localhost:5173`. Backend health check: `http://localhost:8000/api/health/`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health/` | Health check |
| POST | `/api/ingest/sap/` | Upload SAP fuel CSV |
| POST | `/api/ingest/utility/` | Upload utility electricity CSV |
| POST | `/api/ingest/travel/` | Upload travel JSON |
| GET | `/api/batches/?client_slug=acme-corp` | List ingestion batches |
| GET | `/api/records/?batch_id=X&status=PENDING_REVIEW` | List emission records |
| GET | `/api/records/{id}/` | Record detail |
| PATCH | `/api/records/{id}/review/` | Approve, reject, or flag a record |
| GET | `/api/records/{id}/audit-log/` | Full audit history for a record |

## Documentation

- `MODEL.md`: data model design and field decisions
- `DECISIONS.md`: source format choices, scope assignments, and PM questions
- `TRADEOFFS.md`: what was deliberately not built and why
- `SOURCES.md`: real-world format research for SAP, utility, and travel data

## Assignment Mapping

- Data model quality: see `MODEL.md`
- Decision defense: see `DECISIONS.md`
- Source realism: see `SOURCES.md`
- Analyst UX: review dashboard at `/review`
- What was cut: see `TRADEOFFS.md`
