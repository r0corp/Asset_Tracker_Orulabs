from tests.conftest import get_csrf_token, login_as


def create_role_via_ui(admin_client, name, description=""):

    token = get_csrf_token(admin_client, "/roles/add")

    admin_client.post(
        "/roles/add",
        data={
            "name": name,
            "description": description,
            "csrf_token": token,
        },
        follow_redirects=True,
    )


def set_permissions(admin_client, app, role_name, object_name, **actions):

    with app.app_context():

        from app.models import Role

        role = Role.query.filter_by(name=role_name).first()
        role_id = role.id

    token = get_csrf_token(admin_client, f"/roles/{role_id}/permissions")

    data = {"csrf_token": token}

    for action, allowed in actions.items():

        if allowed:
            data[f"perm_{object_name}_{action}"] = "on"

    admin_client.post(
        f"/roles/{role_id}/permissions",
        data=data,
        follow_redirects=True,
    )

    return role_id


def make_user_with_role(app, username, role_name):

    with app.app_context():

        from app.models import User
        from app import db

        if not User.query.filter_by(username=username).first():

            user = User(
                username=username,
                full_name="QA " + username,
                role=role_name,
            )

            user.set_password("test12345")

            db.session.add(user)
            db.session.commit()


def test_new_role_has_no_access_by_default(admin_client, app):

    create_role_via_ui(admin_client, "QA Role Kosong")
    make_user_with_role(app, "qa_empty_role_user", "QA Role Kosong")

    from tests.conftest import login_as

    other_client = app.test_client()
    login_as(other_client, "qa_empty_role_user", "test12345")

    response = other_client.get("/vendors")

    assert response.status_code == 403


def test_role_with_read_only_permission_blocks_mutation(admin_client, app):

    create_role_via_ui(admin_client, "QA Read Only")
    set_permissions(
        admin_client,
        app,
        "QA Read Only",
        "vendor",
        read=True,
    )
    make_user_with_role(app, "qa_readonly_user", "QA Read Only")

    other_client = app.test_client()
    login_as(other_client, "qa_readonly_user", "test12345")

    read_response = other_client.get("/vendors")
    assert read_response.status_code == 200

    # User read-only tidak boleh sampai ke form tambah vendor sama
    # sekali (permission "create" belum diberikan untuk role ini).
    add_page_response = other_client.get("/vendors/add")

    assert add_page_response.status_code == 403


def test_role_with_full_crud_permission_allows_mutation(admin_client, app):

    create_role_via_ui(admin_client, "QA Full Vendor")
    set_permissions(
        admin_client,
        app,
        "QA Full Vendor",
        "vendor",
        create=True,
        read=True,
        edit=True,
        delete=True,
    )
    make_user_with_role(app, "qa_fullvendor_user", "QA Full Vendor")

    other_client = app.test_client()
    login_as(other_client, "qa_fullvendor_user", "test12345")

    token = get_csrf_token(other_client, "/vendors/add")

    response = other_client.post(
        "/vendors/add",
        data={"name": "Vendor QA Allowed", "csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():

        from app.models import Vendor

        assert Vendor.query.filter_by(name="Vendor QA Allowed").first() is not None


def test_administrator_bypasses_permission_matrix(admin_client):

    # administrator tidak pernah diatur izinnya secara eksplisit
    # untuk "vendor" create di test ini, tapi tetap harus bisa akses
    # karena administrator selalu superuser.
    response = admin_client.get("/vendors/add")

    assert response.status_code == 200


def test_cannot_delete_system_role(admin_client, app):

    with app.app_context():

        from app.models import Role

        admin_role = Role.query.filter_by(name="administrator").first()
        role_id = admin_role.id

    token = get_csrf_token(admin_client, "/roles")

    response = admin_client.post(
        f"/roles/{role_id}/delete",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert "cannot be deleted" in response.data.decode().lower()

    with app.app_context():

        from app.models import Role

        assert Role.query.filter_by(name="administrator").first() is not None


def test_cannot_delete_role_still_used_by_users(admin_client, app):

    create_role_via_ui(admin_client, "QA Role Dipakai")
    make_user_with_role(app, "qa_role_dipakai_user", "QA Role Dipakai")

    with app.app_context():

        from app.models import Role

        role = Role.query.filter_by(name="QA Role Dipakai").first()
        role_id = role.id

    token = get_csrf_token(admin_client, "/roles")

    response = admin_client.post(
        f"/roles/{role_id}/delete",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert "still used by" in response.data.decode().lower()


def test_export_roles_returns_excel_file(admin_client):

    response = admin_client.get("/roles/export")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_export_then_import_roundtrip_preserves_permissions(admin_client, app):

    create_role_via_ui(admin_client, "QA Roundtrip")
    set_permissions(
        admin_client,
        app,
        "QA Roundtrip",
        "asset",
        create=True,
        read=True,
    )

    export_response = admin_client.get("/roles/export")

    assert export_response.status_code == 200

    import io

    token = get_csrf_token(admin_client, "/roles/import")

    response = admin_client.post(
        "/roles/import",
        data={
            "csrf_token": token,
            "file": (
                io.BytesIO(export_response.data),
                "roles_export.xlsx",
            ),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "import successful" in response.data.decode().lower()

    with app.app_context():

        from app.models import Role

        role = Role.query.filter_by(name="QA Roundtrip").first()

        permission = role.permission_for("asset")

        assert permission.can_create is True
        assert permission.can_read is True
        assert permission.can_delete is False


def test_dynamic_role_appears_in_user_add_form(admin_client):

    create_role_via_ui(admin_client, "QA Visible Di Form")

    response = admin_client.get("/users/add")

    assert "QA Visible Di Form" in response.data.decode()


def test_roles_page_blocked_for_non_administrator(app):

    make_user_with_role(app, "qa_norole_admin_check", "user")

    other_client = app.test_client()
    login_as(other_client, "qa_norole_admin_check", "test12345")

    response = other_client.get("/roles")

    assert response.status_code == 403
