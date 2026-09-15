import io

from tests.conftest import get_csrf_token, login_as


def test_restore_rejected_without_confirm_text(admin_client, app):

    with app.app_context():

        from app.blueprints.backup import create_backup_zip

        zip_filename = create_backup_zip()

    token = get_csrf_token(admin_client, "/backup")

    response = admin_client.post(
        f"/backup/restore/{zip_filename}",
        data={"confirm_text": "salah", "csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "all uppercase" in response.data.decode().lower()

    # Masih di halaman backup (bukan ke-redirect ke login), artinya
    # restore memang tidak dijalankan.
    assert response.request.path == "/backup"


def test_restore_reverts_data_to_backup_snapshot(admin_client, app):

    # 1. Snapshot kondisi sekarang.
    with app.app_context():

        from app.blueprints.backup import create_backup_zip
        from app.models import Asset

        count_before_temp_asset = Asset.query.count()

        zip_filename = create_backup_zip(prefix="qa_snapshot")

    # 2. Tambah data BARU setelah snapshot diambil.
    token = get_csrf_token(admin_client, "/assets/add")

    admin_client.post(
        "/assets/add",
        data={
            "asset_tag": "QA-RESTORE-TEMP",
            "asset_name": "Asset Sebelum Restore",
            "status": "Active",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    with app.app_context():

        from app.models import Asset

        assert Asset.query.count() == count_before_temp_asset + 1

    # 3. Restore dari snapshot (sebelum asset temp itu ada).
    token = get_csrf_token(admin_client, "/backup")

    response = admin_client.post(
        f"/backup/restore/{zip_filename}",
        data={"confirm_text": "RESTORE", "csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.request.path == "/login"

    # 4. Data harus balik ke kondisi sebelum asset temp ditambahkan.
    with app.app_context():

        from app.models import Asset

        assert Asset.query.count() == count_before_temp_asset

        assert (
            Asset.query.filter_by(asset_tag="QA-RESTORE-TEMP").first()
            is None
        )

    # 5. Backup pengaman otomatis harus dibuat sebelum restore.
    with app.app_context():

        from app.blueprints.backup import get_backup_folder
        import os

        files = os.listdir(get_backup_folder())

        assert any(f.startswith("before_restore_") for f in files)


def test_restore_forces_logout(admin_client, app):

    with app.app_context():

        from app.blueprints.backup import create_backup_zip

        zip_filename = create_backup_zip()

    token = get_csrf_token(admin_client, "/backup")

    admin_client.post(
        f"/backup/restore/{zip_filename}",
        data={"confirm_text": "RESTORE", "csrf_token": token},
        follow_redirects=True,
    )

    # Sesi lama sudah tidak valid lagi - akses halaman terproteksi
    # harus mental ke /login.
    response = admin_client.get("/dashboard")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_restore_blocked_for_non_administrator(app):

    from app.models import User
    from app import db

    with app.app_context():

        if not User.query.filter_by(username="qa_restore_blocked").first():

            user = User(
                username="qa_restore_blocked",
                full_name="QA Restore Blocked",
                role="user",
            )

            user.set_password("test12345")

            db.session.add(user)
            db.session.commit()

    other_client = app.test_client()
    login_as(other_client, "qa_restore_blocked", "test12345")

    response = other_client.get("/backup")

    assert response.status_code == 403


def test_restore_rejects_invalid_zip_upload(admin_client, app):

    with app.app_context():

        from app.models import Asset

        count_before = Asset.query.count()

    token = get_csrf_token(admin_client, "/backup/restore-upload")

    fake_file = io.BytesIO(b"bukan file zip yang valid")

    response = admin_client.post(
        "/backup/restore-upload",
        data={
            "confirm_text": "RESTORE",
            "csrf_token": token,
            "file": (fake_file, "rusak.zip"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "restore failed" in response.data.decode().lower()

    with app.app_context():

        from app.models import Asset

        # Data tidak berubah karena restore-nya gagal/ditolak.
        assert Asset.query.count() == count_before
