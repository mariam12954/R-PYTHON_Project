# Student Management System (FastAPI)

A FastAPI-based backend with JWT auth, role-based access, Redis caching, audit logging, and a simple frontend.

## Project Structure
- app/ (routes, services, models, schemas, core)
- frontendd/ (HTML/CSS/JS UI)
- test/ (pytest suite)

## Setup (Local)
1. Create and activate a virtual environment.
2. Install dependencies:
   - pip install -r requirements.txt
3. Run the API:
   - python -m uvicorn app.main:app --reload
4. Open the UI:
   - http://127.0.0.1:8000

## Docker
1. Build and run:
   - docker compose up --build
2. Stop:
   - docker compose down

## Testing
- pytest

## Caching Performance Check (Redis)
This project uses cache-aside and invalidates on create/update/delete.
You can measure a simple improvement by timing the first (cold) request vs repeated (warm) requests.

PowerShell example:
- Measure-Command { curl http://127.0.0.1:8000/students/?limit=50 -H "Authorization: Bearer <ADMIN_TOKEN>" }
- Measure-Command { curl http://127.0.0.1:8000/students/?limit=50 -H "Authorization: Bearer <ADMIN_TOKEN>" }

The second call should be faster because it is served from Redis. If needed, restart Redis to clear cache:
- docker compose restart redis

## Monitoring Dashboard
- Use the Monitoring page in the UI (admin only).
- It displays request counts, average response time, error rate, recent errors, and system health.

## Team Members and Roles
- TODO:   - Role
- TODO:   - Role
- TODO:   - Role
- TODO:   - Role
- TODO:   - Role
- TODO:   - Role
