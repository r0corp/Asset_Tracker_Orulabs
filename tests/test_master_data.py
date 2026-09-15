from tests.conftest import get_csrf_token


def test_add_and_delete_vendor(admin_client, app):

    token = get_csrf_token(admin_client, "/vendors/add")

    admin_client.post(
        "/vendors/add",
        data={
            "name": "Vendor QA Test",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    with app.app_context():

        from app.models import Vendor

        vendor = Vendor.query.filter_by(name="Vendor QA Test").first()

        assert vendor is not None
        vendor_id = vendor.id

    token = get_csrf_token(admin_client, "/vendors")

    response = admin_client.post(
        f"/vendors/{vendor_id}/delete",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():

        from app.models import Vendor

        assert Vendor.query.filter_by(name="Vendor QA Test").first() is None


def test_add_category_appears_in_list(admin_client):

    token = get_csrf_token(admin_client, "/categories/add")

    admin_client.post(
        "/categories/add",
        data={
            "name": "Kategori QA Test",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    response = admin_client.get("/categories")

    assert "Kategori QA Test" in response.data.decode()
