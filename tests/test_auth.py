from tests.conftest import get_csrf_token, login_as


def test_dashboard_requires_login(client):

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page_accessible(client):

    response = client.get("/login")

    assert response.status_code == 200


def test_login_wrong_password(client):

    response = login_as(client, "admin", "salah-password")

    assert response.status_code == 200
    assert "Incorrect username or password" in response.data.decode()


def test_login_success_redirects_to_dashboard(client):

    response = login_as(client, "admin", "admin123")

    assert response.status_code == 200
    assert response.request.path == "/dashboard"


def test_post_without_csrf_token_is_rejected(admin_client):

    response = admin_client.post(
        "/vendors/999999/delete",
    )

    assert response.status_code == 400


def test_logout_locks_access_again(admin_client):

    response = admin_client.get("/dashboard")
    assert response.status_code == 200

    admin_client.get("/logout", follow_redirects=True)

    response = admin_client.get("/dashboard")
    assert response.status_code == 302


def test_public_verify_page_needs_no_login(client):

    response = client.get("/verify/movement/999999/999999")

    assert response.status_code == 404
