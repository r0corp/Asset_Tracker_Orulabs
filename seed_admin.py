from app import create_app, db
from app.models import User, ROLE_ADMINISTRATOR


app = create_app()

with app.app_context():

    if User.query.filter_by(username="admin").first():

        print("User 'admin' sudah ada, dilewati.")

    else:

        user = User(
            username="admin",
            full_name="Administrator",
            role=ROLE_ADMINISTRATOR,
        )

        user.set_password("admin123")

        db.session.add(user)
        db.session.commit()

        print("User administrator awal dibuat: admin / admin123")
        print("Segera login dan ganti password ini.")
