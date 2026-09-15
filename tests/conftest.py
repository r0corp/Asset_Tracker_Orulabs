import os
import re
import shutil
import tempfile

import pytest

db_fd, db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RATELIMIT_ENABLED"] = "False"

backup_test_dir = tempfile.mkdtemp(prefix="asset_tracker_test_backups_")
branding_test_dir = tempfile.mkdtemp(prefix="asset_tracker_test_branding_")

from app import create_app, db as _db  # noqa: E402
from app.models import (  # noqa: E402
    User,
    Role,
    Permission,
    ROLE_ADMINISTRATOR,
    ROLE_ADMIN,
    ROLE_USER,
    PERMISSION_OBJECT_KEYS,
)


@pytest.fixture(scope="session")
def app():

    application = create_app()

    application.config.update(
        TESTING=True,
        BACKUP_FOLDER=backup_test_dir,
        BRANDING_UPLOAD_FOLDER=branding_test_dir,
    )

    with application.app_context():

        _db.create_all()

        if not User.query.filter_by(username="admin").first():

            user = User(
                username="admin",
                full_name="Administrator",
                role=ROLE_ADMINISTRATOR,
            )

            user.set_password("admin123")

            _db.session.add(user)
            _db.session.commit()

        if not Role.query.first():

            # Sama seperti seed_roles.py: administrator/admin/user
            # semua dapat izin penuh secara default, supaya perilaku
            # test tetap konsisten dengan default aplikasi nyata.
            for role_name in (ROLE_ADMINISTRATOR, ROLE_ADMIN, ROLE_USER):

                role = Role(
                    name=role_name,
                    is_system=(role_name == ROLE_ADMINISTRATOR),
                )

                _db.session.add(role)
                _db.session.flush()

                for object_name in PERMISSION_OBJECT_KEYS:

                    _db.session.add(
                        Permission(
                            role_id=role.id,
                            object_name=object_name,
                            can_create=True,
                            can_read=True,
                            can_edit=True,
                            can_delete=True,
                        )
                    )

            _db.session.commit()

    yield application

    with application.app_context():
        _db.engine.dispose()

    os.close(db_fd)

    try:
        os.unlink(db_path)
    except PermissionError:
        pass

    shutil.rmtree(backup_test_dir, ignore_errors=True)
    shutil.rmtree(branding_test_dir, ignore_errors=True)


@pytest.fixture
def db(app):
    """
    Mengembalikan objek db langsung, TANPA membuka app_context
    untuk seluruh durasi test. Membuka app_context di sini dan
    membiarkannya terbuka selama test client juga melakukan
    request akan membuat Flask menimpa app_context yang sama
    untuk tiap request (bukan push context baru per-request),
    sehingga `g` (dan cache current_user milik Flask-Login di
    dalamnya) ikut "bocor" antar request/antar user di test yang
    sama. Test yang butuh query langsung harus membuka
    `with app.app_context():` sendiri, di luar pemanggilan
    client.get/post.
    """

    return _db


@pytest.fixture
def client(app):

    return app.test_client()


def get_csrf_token(client, url):

    response = client.get(url)

    match = re.search(
        r'name="csrf_token" value="([^"]+)"',
        response.data.decode(),
    )

    return match.group(1) if match else None


def login_as(client, username, password):

    token = get_csrf_token(client, "/login")

    return client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": token,
        },
        follow_redirects=True,
    )


@pytest.fixture
def admin_client(client):

    login_as(client, "admin", "admin123")

    return client
