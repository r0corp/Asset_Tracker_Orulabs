from tests.conftest import get_csrf_token


def test_add_movement_updates_asset_location(admin_client, app):

    token = get_csrf_token(admin_client, "/assets/add")

    admin_client.post(
        "/assets/add",
        data={
            "asset_tag": "QA-MOVE-001",
            "asset_name": "Laptop Movement Test",
            "status": "Active",
            "location": "Office",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    with app.app_context():

        from app.models import Asset

        asset = Asset.query.filter_by(asset_tag="QA-MOVE-001").first()
        asset_id = asset.id

        assert asset.location == "Office"

    token = get_csrf_token(admin_client, f"/assets/{asset_id}/movement/add")

    response = admin_client.post(
        f"/assets/{asset_id}/movement/add",
        data={
            "movement_date": "2026-01-15",
            "from_location": "Office",
            "to_location": "Warehouse",
            "from_department": "IT",
            "to_department": "IT",
            "from_pic": "Budi",
            "to_pic": "Budi",
            "reason": "QA test movement",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():

        from app.models import Asset, AssetMovement

        asset = Asset.query.get(asset_id)

        assert asset.location == "Warehouse"
        assert AssetMovement.query.filter_by(asset_id=asset_id).count() == 1


def test_global_movements_marks_latest_as_current(admin_client, app):

    with app.app_context():

        from app.models import Asset

        asset = Asset.query.filter_by(asset_tag="QA-MOVE-001").first()
        asset_id = asset.id

    token = get_csrf_token(admin_client, f"/assets/{asset_id}/movement/add")

    admin_client.post(
        f"/assets/{asset_id}/movement/add",
        data={
            "movement_date": "2026-02-01",
            "from_location": "Warehouse",
            "to_location": "Server Room",
            "from_department": "IT",
            "to_department": "IT",
            "from_pic": "Budi",
            "to_pic": "Rina",
            "reason": "QA test movement 2",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    response = admin_client.get("/assets/movements?search=QA-MOVE-001")
    html = response.data.decode()

    assert response.status_code == 200
    assert "CURRENT" in html or "Current" in html
