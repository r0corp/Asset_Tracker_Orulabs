import pytest

from tests.conftest import get_csrf_token, login_as


@pytest.fixture
def user_client(app):

    with app.app_context():

        from app import db
        from app.models import User

        if not User.query.filter_by(username="qa_user").first():

            user = User(
                username="qa_user",
                full_name="QA User",
                role="user",
            )

            user.set_password("test123")

            db.session.add(user)
            db.session.commit()

    fresh_client = app.test_client()

    login_as(fresh_client, "qa_user", "test123")

    return fresh_client


def test_administrator_can_access_user_management(admin_client):

    response = admin_client.get("/users")

    assert response.status_code == 200


def test_administrator_can_access_menu_management(admin_client):

    response = admin_client.get("/menus")

    assert response.status_code == 200


def test_regular_user_blocked_from_user_management(user_client):

    response = user_client.get("/users")

    assert response.status_code == 403


def test_regular_user_blocked_from_menu_management(user_client):

    response = user_client.get("/menus")

    assert response.status_code == 403


def test_regular_user_can_still_access_vendors(user_client):

    response = user_client.get("/vendors")

    assert response.status_code == 200


def test_admin_cannot_delete_own_account(admin_client, app):

    with app.app_context():

        from app.models import User

        admin = User.query.filter_by(username="admin").first()
        admin_id = admin.id

    token = get_csrf_token(admin_client, "/users/add")

    response = admin_client.post(
        f"/users/{admin_id}/delete",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "cannot delete your own account" in response.data.decode().lower()
