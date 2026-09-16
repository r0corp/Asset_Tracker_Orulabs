from datetime import datetime

from flask import Flask, flash, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel, gettext as _, lazy_gettext as _l


db = SQLAlchemy()

migrate = Migrate()

login_manager = LoginManager()

csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)

babel = Babel()


def get_locale():
    """
    Urutan penentuan bahasa: pilihan manual user (tersimpan di
    session lewat /language/<kode>) -> bahasa browser yang cocok
    -> default aplikasi (Inggris).
    """

    from flask import current_app

    languages = current_app.config["LANGUAGES"]

    chosen = session.get("language")

    if chosen in languages:
        return chosen

    return (
        request.accept_languages.best_match(languages.keys())
        or current_app.config["BABEL_DEFAULT_LOCALE"]
    )


def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)

    migrate.init_app(app, db)

    login_manager.init_app(app)

    login_manager.login_view = "main.login"

    login_manager.login_message = _l(
        "Please log in to access this page."
    )

    login_manager.login_message_category = "warning"

    csrf.init_app(app)

    limiter.init_app(app)

    babel.init_app(app, locale_selector=get_locale)

    from .blueprints import main

    app.register_blueprint(main)

    from . import models

    @app.errorhandler(413)
    def handle_file_too_large(error):

        flash(
            _("The uploaded file is too large (maximum 5 MB)."),
            "danger",
        )

        return redirect(
            request.referrer
            or url_for("main.dashboard")
        )

    @login_manager.user_loader
    def load_user(user_id):

        return models.User.query.get(
            int(user_id)
        )

    @app.context_processor
    def inject_nav_menu():

        if not current_user.is_authenticated:
            return {"nav_menu": []}

        role = current_user.role

        top_items = (
            models.MenuItem.query
            .filter_by(
                parent_id=None,
                is_active=True,
            )
            .order_by(
                models.MenuItem.order,
                models.MenuItem.id,
            )
            .all()
        )

        nav_menu = []

        for item in top_items:

            if not item.is_visible_to(role):
                continue

            children = [
                child
                for child in item.children
                if child.is_active
                and child.is_visible_to(role)
            ]

            nav_menu.append({
                "item": item,
                "children": children,
            })

        return {"nav_menu": nav_menu}

    @app.context_processor
    def inject_online_users():

        if (
            not current_user.is_authenticated
            or current_user.role != models.ROLE_ADMINISTRATOR
        ):
            return {"online_users": []}

        online_users = sorted(
            (
                user
                for user in models.User.query.all()
                if user.id != current_user.id
                and user.is_online
            ),
            key=lambda user: user.full_name,
        )

        return {"online_users": online_users}

    @app.context_processor
    def inject_app_setting():

        from .blueprints.app_settings import get_app_setting

        return {"app_setting": get_app_setting()}

    @app.context_processor
    def inject_now():

        return {"now": datetime.utcnow}

    @app.context_processor
    def inject_language():

        return {
            "current_language": get_locale(),
            "available_languages": app.config["LANGUAGES"],
        }

    return app