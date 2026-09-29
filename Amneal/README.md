# Amneal Login Application

Full-stack starter application with:

- React + Vite frontend
- FastAPI backend with JWT authentication
- PostgreSQL database
- Idempotent database automation for database creation, table creation, table alteration, and dummy data

## Run with Docker

Requirements: Docker Desktop with Compose.

```powershell
docker compose up --build
```

Open <http://localhost:5173>. The seeded account is:

- Email: `demo@amneal.com`
- Password: `Demo@123`

The API is available at <http://localhost:8000> and its OpenAPI docs at <http://localhost:8000/docs>.

## Run locally

Start PostgreSQL, then run the database automation:

```powershell
python backend\scripts\bootstrap_db.py
```

Run the API:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Set `DATABASE_URL`, `JWT_SECRET`, and `CORS_ORIGINS` in `.env` as needed. See `.env.example`.
