def register_user(client, username, email, role):
    r = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": "pass123",
        "role": role,
    })
    assert r.status_code == 201


def login_user(client, username):
    r = client.post("/auth/login", json={"username": username, "password": "pass123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_monitoring_admin_only(client):
    register_user(client, "adminmon", "adminmon@test.com", "admin")
    register_user(client, "studmon", "studmon@test.com", "student")

    admin_token = login_user(client, "adminmon")
    student_token = login_user(client, "studmon")

    r_forbidden = client.get("/monitoring/", headers={"Authorization": f"Bearer {student_token}"})
    assert r_forbidden.status_code == 403

    r_ok = client.get("/monitoring/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r_ok.status_code == 200
    payload = r_ok.json()
    assert "total_requests" in payload
    assert "avg_response_ms" in payload
    assert "endpoints" in payload
