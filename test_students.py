def register_user(client, username, email, role):
    r = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": "pass123",
        "role": role,
    })
    assert r.status_code == 201
    return r.json()["id"]


def login_user(client, username):
    r = client.post("/auth/login", json={"username": username, "password": "pass123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def get_admin_headers(client):
    register_user(client, "admin", "admin@test.com", "admin")
    token = login_user(client, "admin")
    return {"Authorization": f"Bearer {token}"}


def create_student_profile(client, headers, user_id, full_name="Student One", department="CS", gpa=3.5, year=2):
    r = client.post("/students/", headers=headers, json={
        "full_name": full_name,
        "department": department,
        "gpa": gpa,
        "year": year,
        "user_id": user_id,
    })
    assert r.status_code == 201
    return r.json()


def test_create_and_get_student(client):
    headers = get_admin_headers(client)
    user_id = register_user(client, "student1", "student1@test.com", "student")
    created = create_student_profile(client, headers, user_id, full_name="Ahmed Ali")
    sid = created["id"]
    r2 = client.get(f"/students/{sid}", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["full_name"] == "Ahmed Ali"


def test_delete_student_as_admin(client):
    headers = get_admin_headers(client)
    user_id = register_user(client, "student2", "student2@test.com", "student")
    created = create_student_profile(client, headers, user_id, full_name="Sara")
    sid = created["id"]
    r2 = client.delete(f"/students/{sid}", headers=headers)
    assert r2.status_code == 200


def test_student_search_and_audit_log(client):
    headers = get_admin_headers(client)
    user_id = register_user(client, "student3", "student3@test.com", "student")
    create_student_profile(client, headers, user_id, full_name="Mona Hassan", department="AI", gpa=3.8, year=3)

    r = client.get("/students/?search=Mona", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["full_name"] == "Mona Hassan"

    logs = client.get("/audit-logs/", headers=headers)
    assert logs.status_code == 200
    assert any(log["action"] == "CREATE" for log in logs.json())


def test_student_cannot_list_students(client):
    register_user(client, "studlist", "studlist@test.com", "student")
    token = login_user(client, "studlist")
    r = client.get("/students/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_student_profile_access_control(client):
    headers = get_admin_headers(client)
    user_id_1 = register_user(client, "student4", "student4@test.com", "student")
    user_id_2 = register_user(client, "student5", "student5@test.com", "student")
    student_1 = create_student_profile(client, headers, user_id_1, full_name="User One")
    student_2 = create_student_profile(client, headers, user_id_2, full_name="User Two")

    token = login_user(client, "student4")
    headers_student = {"Authorization": f"Bearer {token}"}
    me = client.get("/students/me", headers=headers_student)
    assert me.status_code == 200
    assert me.json()["user_id"] == user_id_1

    other = client.get(f"/students/{student_2['id']}", headers=headers_student)
    assert other.status_code == 403


def test_update_student_creates_audit_log(client):
    headers = get_admin_headers(client)
    user_id = register_user(client, "student6", "student6@test.com", "student")
    created = create_student_profile(client, headers, user_id, full_name="Update User", gpa=2.9)
    sid = created["id"]

    update = client.put(f"/students/{sid}", headers=headers, json={"gpa": 3.4})
    assert update.status_code == 200
    assert update.json()["gpa"] == 3.4

    logs = client.get("/audit-logs/", headers=headers)
    assert logs.status_code == 200
    assert any(log["action"] == "UPDATE" and log["target_student_id"] == sid for log in logs.json())


def test_invalid_gpa_rejected(client):
    headers = get_admin_headers(client)
    user_id = register_user(client, "student7", "student7@test.com", "student")
    r = client.post("/students/", headers=headers, json={
        "full_name": "Bad GPA",
        "department": "CS",
        "gpa": 4.9,
        "year": 2,
        "user_id": user_id,
    })
    assert r.status_code == 422


def test_filter_by_gpa(client):
    headers = get_admin_headers(client)
    user_id_1 = register_user(client, "student8", "student8@test.com", "student")
    user_id_2 = register_user(client, "student9", "student9@test.com", "student")
    create_student_profile(client, headers, user_id_1, full_name="Low GPA", gpa=2.0)
    create_student_profile(client, headers, user_id_2, full_name="High GPA", gpa=3.9)

    r = client.get("/students/?min_gpa=3.5", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["full_name"] == "High GPA"


def test_student_cannot_delete_student(client):
    headers = get_admin_headers(client)
    user_id = register_user(client, "student10", "student10@test.com", "student")
    created = create_student_profile(client, headers, user_id, full_name="Delete Guard")
    sid = created["id"]

    token = login_user(client, "student10")
    r = client.delete(f"/students/{sid}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_get_missing_student_returns_404(client):
    headers = get_admin_headers(client)
    r = client.get("/students/9999", headers=headers)
    assert r.status_code == 404


def test_update_missing_student_returns_404(client):
    headers = get_admin_headers(client)
    r = client.put("/students/9999", headers=headers, json={"gpa": 3.2})
    assert r.status_code == 404


def test_delete_missing_student_returns_404(client):
    headers = get_admin_headers(client)
    r = client.delete("/students/9999", headers=headers)
    assert r.status_code == 404


def test_me_without_profile_returns_404(client):
    register_user(client, "noprof", "noprof@test.com", "student")
    token = login_user(client, "noprof")
    r = client.get("/students/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404