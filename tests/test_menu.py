from tests.conftest import get_csrf_token


def add_menu(client, **overrides):

    data = {
        "label": "Menu QA",
        "url": "/dashboard",
        "icon": "",
        "order": "0",
        "parent_id": "",
        "is_active": "1",
    }

    data.update(overrides)

    token = get_csrf_token(client, "/menus/add")
    data["csrf_token"] = token

    return client.post(
        "/menus/add",
        data=data,
        follow_redirects=True,
    )


def test_new_menu_item_appears_in_navbar(admin_client):

    add_menu(admin_client, label="Menu QA Unik")

    response = admin_client.get("/dashboard")

    assert "Menu QA Unik" in response.data.decode()


def test_menu_with_children_renders_as_dropdown(admin_client, app):

    add_menu(admin_client, label="Grup QA", url="")

    with app.app_context():

        from app.models import MenuItem

        parent = MenuItem.query.filter_by(label="Grup QA").first()
        parent_id = parent.id

    add_menu(
        admin_client,
        label="Anak QA",
        url="/vendors",
        parent_id=str(parent_id),
    )

    response = admin_client.get("/dashboard")
    html = response.data.decode()

    assert "Grup QA" in html
    assert "Anak QA" in html


def test_inactive_menu_hidden_from_navbar(admin_client):

    add_menu(admin_client, label="Menu Nonaktif QA", is_active="0")

    response = admin_client.get("/dashboard")

    assert "Menu Nonaktif QA" not in response.data.decode()


def test_role_restricted_menu_hidden_from_other_roles(admin_client, app):

    add_menu(admin_client, label="Menu Admin Saja QA", roles="administrator")

    with app.app_context():

        from app.models import User

        if not User.query.filter_by(username="qa_menu_user").first():

            user = User(
                username="qa_menu_user",
                full_name="QA Menu User",
                role="user",
            )

            user.set_password("test123")

            from app import db

            db.session.add(user)
            db.session.commit()

    from tests.conftest import login_as

    # Client baru dan terpisah dari admin_client, supaya sesi
    # login tidak saling menimpa (admin_client tetap login admin).
    other_client = app.test_client()

    login_as(other_client, "qa_menu_user", "test123")

    response = other_client.get("/dashboard")

    assert "Menu Admin Saja QA" not in response.data.decode()


def test_delete_menu_removes_it_from_navbar(admin_client, app):

    add_menu(admin_client, label="Menu Akan Dihapus QA")

    with app.app_context():

        from app.models import MenuItem

        item = MenuItem.query.filter_by(label="Menu Akan Dihapus QA").first()
        item_id = item.id

    token = get_csrf_token(admin_client, "/menus")

    admin_client.post(
        f"/menus/{item_id}/delete",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    response = admin_client.get("/dashboard")

    assert "Menu Akan Dihapus QA" not in response.data.decode()
