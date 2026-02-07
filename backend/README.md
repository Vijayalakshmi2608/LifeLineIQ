# Rural Health Triage API

FastAPI backend for LifeLineIQ rural health triage.

## Setup

1. Copy `.env.example` to `.env` and fill in values.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server:

```bash
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `POST /triage`
- `GET /facilities`

## Notes

- Uses async SQLAlchemy with PostgreSQL.
- Includes basic rate limiting and request IDs.
