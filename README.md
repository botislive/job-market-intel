# Workforce Market Intelligence

Job market intelligence dashboard for staffing and recruitment teams. Aggregates listings from free JSON APIs, RSS feeds, and LinkedIn guest search.

## Data sources

| Source | Type |
|--------|------|
| Remotive | JSON API |
| RemoteOK | JSON API |
| Arbeitnow | JSON API |
| Jobicy | JSON API |
| We Work Remotely | RSS |
| Himalayas | RSS |
| Jobicy | RSS |
| LinkedIn | Guest HTML API |
| Fortune 100 Careers | Career pages for [Fortune Global 500 top 100](backend/data/fortune100_careers.json) (Workday, Amazon Jobs, Microsoft PCSX APIs where publicly available) |

## Quick start

### Backend

```bash
cd backend
python3.11 -m venv .venv   # use 3.11 or 3.12 — not 3.14
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Or run both servers: `./start.sh`

### Seed data (run before demo)

```bash
cd backend && source .venv/bin/activate
python ../scripts/run_scrape.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — click **Sync Market Data** to refresh.

## Demo talking points (Tekwissen HR)

- **Hot skills** — which technologies appear most in live postings
- **Top hiring companies** — sales lead signals for staffing outreach
- **Source breakdown** — multi-channel market coverage
- **Role-specific LinkedIn pulls** — SAP, Java, DevOps, ServiceNow for India & US
