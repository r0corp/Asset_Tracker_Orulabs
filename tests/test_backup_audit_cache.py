from tests.conftest import get_csrf_token


def test_backup_page_accessible_by_administrator(admin_client):

    response = admin_client.get("/backup")

    assert response.status_code == 200


def test_backup_create_and_download(admin_client, app):

    token = get_csrf_token(admin_client, "/backup")

    response = admin_client.post(
        "/backup/create",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "created successfully" in response.data.decode().lower()

    with app.app_context():

        from app.blueprints.backup import get_backup_folder
        import os

        folder = get_backup_folder()

        files = [f for f in os.listdir(folder) if f.endswith(".zip")]

        assert len(files) >= 1

        latest = sorted(files)[-1]

    dl = admin_client.get(f"/backup/download/{latest}")

    assert dl.status_code == 200
    assert dl.headers["Content-Type"] in (
        "application/zip",
        "application/x-zip-compressed",
    )

    # Bersihkan file backup hasil test. Di Windows, file yang baru saja
    # di-stream lewat send_file kadang masih dianggap "in use" sesaat
    # setelah response selesai - itu bukan bug fungsional, jadi
    # pembersihan ini dibuat best-effort saja (tidak menggagalkan test).
    try:

        token2 = get_csrf_token(admin_client, "/backup")

        admin_client.post(
            f"/backup/delete/{latest}",
            data={"csrf_token": token2},
            follow_redirects=True,
        )

    except Exception:
        pass


def test_backup_blocked_for_non_administrator(client, app):

    from tests.conftest import login_as
    from app.models import User
    from app import db

    with app.app_context():

        if not User.query.filter_by(username="qa_backup_user").first():

            user = User(
                username="qa_backup_user",
                full_name="QA Backup User",
                role="user",
            )

            user.set_password("test12345")

            db.session.add(user)
            db.session.commit()

    login_as(client, "qa_backup_user", "test12345")

    response = client.get("/backup")

    assert response.status_code == 403


def test_clear_cache_page_accessible_by_any_role(admin_client):

    response = admin_client.get("/clear-cache")

    assert response.status_code == 200


def test_audit_log_records_asset_creation(admin_client, app):

    token = get_csrf_token(admin_client, "/assets/add")

    admin_client.post(
        "/assets/add",
        data={
            "asset_tag": "QA-AUDIT-001",
            "asset_name": "Laptop Audit Test",
            "status": "Active",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    response = admin_client.get("/audit-log")

    assert response.status_code == 200
    assert "QA-AUDIT-001" in response.data.decode()


def test_audit_log_blocked_for_non_administrator(client, app):

    from tests.conftest import login_as
    from app.models import User
    from app import db

    with app.app_context():

        if not User.query.filter_by(username="qa_audit_user").first():

            user = User(
                username="qa_audit_user",
                full_name="QA Audit User",
                role="user",
            )

            user.set_password("test12345")

            db.session.add(user)
            db.session.commit()

    login_as(client, "qa_audit_user", "test12345")

    response = client.get("/audit-log")

    assert response.status_code == 403


def test_add_user_rejects_short_password(admin_client, app):

    token = get_csrf_token(admin_client, "/users/add")

    response = admin_client.post(
        "/users/add",
        data={
            "username": "qa_shortpw",
            "full_name": "QA Short Password",
            "role": "user",
            "password": "123",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "at least" in response.data.decode().lower()

    with app.app_context():

        from app.models import User

        assert User.query.filter_by(username="qa_shortpw").first() is None
