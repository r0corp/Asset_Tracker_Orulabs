from app import create_app, db
from app.models import (
    Role,
    Permission,
    PERMISSION_OBJECT_KEYS,
    ROLE_ADMINISTRATOR,
    ROLE_ADMIN,
    ROLE_USER,
)


app = create_app()

with app.app_context():

    if Role.query.first():

        print("Role sudah ada data, dilewati.")

    else:

        roles = {
            ROLE_ADMINISTRATOR: Role(
                name=ROLE_ADMINISTRATOR,
                description="Akses penuh ke seluruh sistem (bawaan, tidak bisa dihapus).",
                is_system=True,
            ),
            ROLE_ADMIN: Role(
                name=ROLE_ADMIN,
                description="Akses penuh ke data operasional (asset, mutasi, master data).",
            ),
            ROLE_USER: Role(
                name=ROLE_USER,
                description="Akses standar untuk penggunaan sehari-hari.",
            ),
        }

        db.session.add_all(roles.values())
        db.session.flush()

        # Mempertahankan perilaku yang sudah berjalan sebelum fitur
        # matrix ini ada: administrator/admin/user semua bisa CRUD
        # penuh di semua object bisnis. Administrator sekarang bisa
        # mengubah ini per role lewat halaman Manajemen Role.
        for role in roles.values():

            for object_name in PERMISSION_OBJECT_KEYS:

                db.session.add(
                    Permission(
                        role_id=role.id,
                        object_name=object_name,
                        can_create=True,
                        can_read=True,
                        can_edit=True,
                        can_delete=True,
                    )
                )

        db.session.commit()

        print("Role & permission default berhasil dibuat.")
