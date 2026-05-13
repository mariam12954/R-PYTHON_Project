import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

VENV_SITE_PACKAGES = os.path.join(PROJECT_ROOT, ".venv", "Lib", "site-packages")
if os.path.isdir(VENV_SITE_PACKAGES) and VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

from app.models.user import User

def test_register(client):
    r = client.post("/auth/register", json={
        "username": "admin1", "email": "admin@test.com",
        "password": "admin123", "role": "admin"
    })
    assert r.status_code == 201
    assert r.json()["username"] == "admin1"

def test_login(client):
    client.post("/auth/register", json={
        "username": "admin1", "email": "admin@test.com",
        "password": "admin123", "role": "admin"
    })
    r = client.post("/auth/login", json={"username": "admin1", "password": "admin123"})
    assert r.status_code == 200
    assert "access_token" in r.json()

def test_wrong_password(client):
    client.post("/auth/register", json={
        "username": "user1", "email": "user@test.com",
        "password": "correct", "role": "student"
    })
    r = client.post("/auth/login", json={"username": "user1", "password": "wrong"})
    assert r.status_code == 401


def test_register_duplicate_username(client):
    client.post("/auth/register", json={
        "username": "dupe", "email": "dupe1@test.com",
        "password": "pass123", "role": "student"
    })
    r = client.post("/auth/register", json={
        "username": "dupe", "email": "dupe2@test.com",
        "password": "pass123", "role": "student"
    })
    assert r.status_code == 400


def test_register_duplicate_email(client):
    client.post("/auth/register", json={
        "username": "usera", "email": "dupemail@test.com",
        "password": "pass123", "role": "student"
    })
    r = client.post("/auth/register", json={
        "username": "userb", "email": "dupemail@test.com",
        "password": "pass123", "role": "student"
    })
    assert r.status_code == 400


def test_login_inactive_user(client, db):
    client.post("/auth/register", json={
        "username": "inactive", "email": "inactive@test.com",
        "password": "pass123", "role": "student"
    })
    user = db.query(User).filter(User.username == "inactive").first()
    user.is_active = False
    db.commit()
    r = client.post("/auth/login", json={"username": "inactive", "password": "pass123"})
    assert r.status_code == 403


def test_get_me_requires_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_get_me_success(client):
    client.post("/auth/register", json={
        "username": "meuser", "email": "meuser@test.com",
        "password": "pass123", "role": "student"
    })
    login = client.post("/auth/login", json={"username": "meuser", "password": "pass123"})
    token = login.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "meuser"