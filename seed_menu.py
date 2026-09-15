from app import create_app, db
from app.models import MenuItem, ROLE_ADMINISTRATOR


app = create_app()

with app.app_context():

    if MenuItem.query.first():

        print("Menu sudah ada data, dilewati.")

    else:

        dashboard = MenuItem(
            label="Dashboard",
            icon="bi-speedometer2",
            url="/dashboard",
            order=10,
        )

        asset = MenuItem(
            label="Asset",
            icon="bi-box-seam",
            url="/",
            order=20,
        )

        laporan_mutasi = MenuItem(
            label="Movement Report",
            icon="bi-arrow-left-right",
            url="/assets/movements/report",
            order=30,
        )

        warranty = MenuItem(
            label="Warranty",
            icon="bi-shield-check",
            url="/warranty",
            order=40,
        )

        master_data = MenuItem(
            label="Master Data",
            icon="bi-database",
            url=None,
            order=50,
        )

        company = MenuItem(
            label="Company",
            icon="bi-building",
            url="/company",
            order=60,
        )

        manajemen_user = MenuItem(
            label="User Management",
            icon="bi-people",
            url="/users",
            order=70,
            roles=ROLE_ADMINISTRATOR,
        )

        manajemen_menu = MenuItem(
            label="Menu Management",
            icon="bi-list-ul",
            url="/menus",
            order=80,
            roles=ROLE_ADMINISTRATOR,
        )

        db.session.add_all([
            dashboard,
            asset,
            laporan_mutasi,
            warranty,
            master_data,
            company,
            manajemen_user,
            manajemen_menu,
        ])

        db.session.flush()

        children = [
            MenuItem(
                label="Category",
                url="/categories",
                order=10,
                parent_id=master_data.id,
            ),
            MenuItem(
                label="Location",
                url="/locations",
                order=20,
                parent_id=master_data.id,
            ),
            MenuItem(
                label="Department",
                url="/departments",
                order=30,
                parent_id=master_data.id,
            ),
            MenuItem(
                label="Vendor",
                url="/vendors",
                order=40,
                parent_id=master_data.id,
            ),
        ]

        db.session.add_all(children)
        db.session.commit()

        print("Menu default berhasil dibuat.")
