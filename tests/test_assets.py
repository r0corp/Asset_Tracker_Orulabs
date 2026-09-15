from tests.conftest import get_csrf_token


def test_add_asset(admin_client, app):

    token = get_csrf_token(admin_client, "/assets/add")

    response = admin_client.post(
        "/assets/add",
        data={
            "asset_tag": "QA-TEST-001",
            "asset_name": "Laptop QA Test",
            "status": "Active",
            "purchase_price": "1234.56",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():

        from app.models import Asset

        asset = Asset.query.filter_by(asset_tag="QA-TEST-001").first()

        assert asset is not None
        assert asset.purchase_price == 1234.56


def test_edit_asset_price_parses_decimal_correctly(admin_client, app):

    with app.app_context():

        from app.models import Asset

        asset = Asset.query.filter_by(asset_tag="QA-TEST-001").first()
        asset_id = asset.id
        asset_tag = asset.asset_tag
        asset_name = asset.asset_name

    token = get_csrf_token(
        admin_client,
        f"/assets/edit/{asset_id}",
    )

    admin_client.post(
        f"/assets/edit/{asset_id}",
        data={
            "asset_tag": asset_tag,
            "asset_name": asset_name,
            "status": "Active",
            "purchase_price": "9999.99",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    with app.app_context():

        from app.models import Asset

        asset = Asset.query.get(asset_id)

        assert asset.purchase_price == 9999.99


def test_asset_list_pagination_stays_within_bounds(admin_client):

    response = admin_client.get("/assets?page=999")

    assert response.status_code == 200


def test_delete_asset_requires_csrf(admin_client, app):

    with app.app_context():

        from app.models import Asset

        asset = Asset.query.filter_by(asset_tag="QA-TEST-001").first()
        asset_id = asset.id

    response = admin_client.post(f"/assets/{asset_id}/delete")

    assert response.status_code == 400
