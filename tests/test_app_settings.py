import io

from tests.conftest import get_csrf_token, login_as


def test_app_settings_page_blocked_for_non_administrator(app):

    from app.models import User
    from app import db

    with app.app_context():

        if not User.query.filter_by(username="qa_settings_blocked").first():

            user = User(
                username="qa_settings_blocked",
                full_name="QA Settings Blocked",
                role="user",
            )

            user.set_password("test12345")

            db.session.add(user)
            db.session.commit()

    other_client = app.test_client()
    login_as(other_client, "qa_settings_blocked", "test12345")

    response = other_client.get("/settings/general")

    assert response.status_code == 403


def test_default_app_name_shown_before_any_settings_saved(admin_client):

    response = admin_client.get("/dashboard")

    assert "Asset Tracker" in response.data.decode()


def test_update_app_name_reflects_on_login_and_sidebar(admin_client, app):

    token = get_csrf_token(admin_client, "/settings/general")

    response = admin_client.post(
        "/settings/general",
        data={
            "app_name": "QA Tracker Kustom",
            "footer_text": "",
            "login_message": "",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "saved successfully" in response.data.decode().lower()

    dashboard_response = admin_client.get("/dashboard")

    assert "QA Tracker Kustom" in dashboard_response.data.decode()

    logout_client = app.test_client()

    login_page = logout_client.get("/login")

    assert "QA Tracker Kustom" in login_page.data.decode()


def test_update_footer_text(admin_client):

    token = get_csrf_token(admin_client, "/settings/general")

    admin_client.post(
        "/settings/general",
        data={
            "app_name": "Asset Tracker",
            "footer_text": "Hak Cipta QA Corp",
            "login_message": "",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    response = admin_client.get("/dashboard")

    assert "Hak Cipta QA Corp" in response.data.decode()


def test_update_login_message(admin_client, app):

    token = get_csrf_token(admin_client, "/settings/general")

    admin_client.post(
        "/settings/general",
        data={
            "app_name": "Asset Tracker",
            "footer_text": "",
            "login_message": "Sistem Internal QA",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    fresh_client = app.test_client()

    response = fresh_client.get("/login")

    assert "Sistem Internal QA" in response.data.decode()


def test_upload_wide_logo_appears_in_sidebar(admin_client):

    token = get_csrf_token(admin_client, "/settings/general")

    fake_logo = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 50)

    response = admin_client.post(
        "/settings/general",
        data={
            "app_name": "Asset Tracker",
            "footer_text": "",
            "login_message": "",
            "logo_wide": (fake_logo, "wide.png"),
            "csrf_token": token,
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200

    dashboard_response = admin_client.get("/dashboard")

    assert "uploads/branding/logo_wide.png" in dashboard_response.data.decode()


def test_remove_wide_logo(admin_client, app):

    with app.app_context():

        from app.blueprints.app_settings import get_app_setting

        setting = get_app_setting()

        assert setting.logo_wide is not None

    token = get_csrf_token(admin_client, "/settings/general")

    admin_client.post(
        "/settings/general",
        data={
            "app_name": "Asset Tracker",
            "footer_text": "",
            "login_message": "",
            "remove_logo_wide": "1",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    with app.app_context():

        from app.blueprints.app_settings import get_app_setting

        setting = get_app_setting()

        assert setting.logo_wide is None


def test_upload_square_logo_used_as_favicon(admin_client):

    token = get_csrf_token(admin_client, "/settings/general")

    fake_logo = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"1" * 50)

    admin_client.post(
        "/settings/general",
        data={
            "app_name": "Asset Tracker",
            "footer_text": "",
            "login_message": "",
            "logo_square": (fake_logo, "square.png"),
            "csrf_token": token,
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    response = admin_client.get("/dashboard")
    html = response.data.decode()

    assert 'rel="icon"' in html
    assert "uploads/branding/logo_square.png" in html


def test_rejects_invalid_logo_extension(admin_client):

    token = get_csrf_token(admin_client, "/settings/general")

    fake_file = io.BytesIO(b"not an image")

    response = admin_client.post(
        "/settings/general",
        data={
            "app_name": "Asset Tracker",
            "footer_text": "",
            "login_message": "",
            "logo_wide": (fake_file, "malware.exe"),
            "csrf_token": token,
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "logo format" in response.data.decode().lower()
