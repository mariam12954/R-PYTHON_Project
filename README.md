# Student Management System (FastAPI)

A FastAPI-based backend with JWT auth, role-based access, Redis caching, audit logging, and a simple frontend.

## Project Structure
- app/ (routes, services, models, schemas, core)
- frontendd/ (HTML/CSS/JS UI)
- test/ (pytest suite)

## Requirements
- Python 3.12+
- Redis (for caching)
- SQLite (default) or PostgreSQL

## Setup (Local)
1. Create and activate a virtual environment.
2. Install dependencies:
   - pip install -r requirements.txt
3. Start Redis (required for caching):
   - docker run -d -p 6379:6379 redis:latest
4. Run the API:
   - python -m uvicorn app.main:app --reload
5. Open the UI:
   - http://127.0.0.1:8000

## Docker
1. Build and run:
   - docker compose up --build
2. Stop:
   - docker compose down

## Testing
- pytest

## JWT Authentication
- Access tokens are generated upon login and must be included in the `Authorization: Bearer <token>` header
- Tokens expire after a configurable duration (default: 30 minutes)
- Token validation ensures user is active and has appropriate role permissions
- See `app/core/security.py` for token creation and validation logic

## Role-Based Access Control (RBAC)
The system supports two roles:
- **admin**: Full access to all endpoints (user management, student management, monitoring, audit logs)
- **student**: Limited access (view own profile, view audit logs filtered to their actions)

Role checks are enforced in service and route layers using JWT claims.

## API Endpoints Quick Reference

### Authentication
- `POST /auth/register` — Register new user
- `POST /auth/login` — Login and get JWT token
- `GET /auth/me` — Get current authenticated user

### Students
- `GET /students/` — List all students (admin only, cacheable)
- `POST /students/` — Create student profile (admin only)
- `GET /students/{id}` — Get student by ID
- `GET /students/me` — Get own student profile (students)
- `PUT /students/{id}` — Update student (admin or self)
- `DELETE /students/{id}` — Delete student (admin only)

### Audit Logs
- `GET /audit-logs/` — View audit logs (filtered by user role)

### Monitoring
- `GET /monitoring/` — View system metrics (admin only)

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
- **Member 1**: JWT & Authentication (Marks: 3) — security.py, auth_service.py, test_auth.py
- **Member 2**: Database & Models (Marks: 2) — database.py, models (User, Student, AuditLog)
- **Member 3**: Validation & Clean Code (Marks: 5) — schemas, code organization, type hints
- **Member 4**: Caching & Performance (Marks: 2) — cache.py, cache-aside pattern, cache invalidation
- **Member 5**: Logging, Monitoring & Testing (Marks: 4) — logging.py, metrics.py, test_monitoring.py, test_students.py
- **Member 6**: Frontend, Docker & Documentation (Marks: 4) — frontendd/, Dockerfile, docker-compose.yml, README
