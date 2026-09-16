"""
Manajemen user (CRUD akun) - khusus administrator.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_babel import gettext as _
from flask_login import current_user

from .. import db
from ..models import User, Role
from ..auth import administrator_required

from . import main
from .helpers import log_action

MIN_PASSWORD_LENGTH = 8


def get_role_names():

    return [
        role.name
        for role in Role.query.order_by(Role.name.asc()).all()
    ]

@main.route("/users")
@administrator_required
def users():

    items = (
        User.query
        .order_by(User.username)
        .all()
    )

    return render_template(
        "master/user/list.html",
        users=items,
    )


@main.route("/users/online-status")
@administrator_required
def users_online_status():
    """
    Dipanggil berkala (polling) lewat JavaScript di halaman User
    Management supaya status online/offline ter-update otomatis
    tanpa reload halaman.
    """

    items = User.query.all()

    return jsonify({
        "users": {
            str(user.id): {
                "online": user.is_online,
                "last_seen": (
                    user.last_seen.isoformat() + "Z"
                    if user.last_seen
                    else None
                ),
            }
            for user in items
        }
    })


@main.route("/users/online-list")
@administrator_required
def users_online_list():
    """
    Dipanggil berkala (polling) oleh dropdown profil di navbar untuk
    menampilkan daftar user lain yang sedang online - lihat
    base.html. Terpisah dari /users/online-status (yang dipakai
    halaman User Management) karena responsnya perlu nama & role,
    bukan cuma status online/offline per id.
    """

    online_users = sorted(
        (
            user
            for user in User.query.all()
            if user.id != current_user.id
            and user.is_online
        ),
        key=lambda user: user.full_name,
    )

    return jsonify({
        "users": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role,
            }
            for user in online_users
        ]
    })


@main.route(
    "/users/add",
    methods=["GET", "POST"],
)
@administrator_required
def add_user():

    if request.method == "POST":

        username = request.form.get(
            "username",
            "",
        ).strip()

        full_name = request.form.get(
            "full_name",
            "",
        ).strip()

        role = request.form.get(
            "role",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        if not username or not full_name or not password:

            flash(
                _("Username, full name, and password are required."),
                "danger",
            )

            return redirect(
                url_for("main.add_user")
            )

        if len(password) < MIN_PASSWORD_LENGTH:

            flash(
                _("Password must be at least %(min_length)s characters.")
                % {"min_length": MIN_PASSWORD_LENGTH},
                "danger",
            )

            return redirect(
                url_for("main.add_user")
            )

        if role not in get_role_names():

            flash(
                _("Invalid role."),
                "danger",
            )

            return redirect(
                url_for("main.add_user")
            )

        if User.query.filter_by(username=username).first():

            flash(
                _("Username is already in use."),
                "danger",
            )

            return redirect(
                url_for("main.add_user")
            )

        user = User(
            username=username,
            full_name=full_name,
            role=role,
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        log_action(
            "create",
            "User",
            entity_label=user.username,
        )

        flash(
            _("User added successfully."),
            "success",
        )

        return redirect(
            url_for("main.users")
        )

    return render_template(
        "master/user/add.html",
        role_choices=get_role_names(),
    )


@main.route(
    "/users/<int:user_id>/edit",
    methods=["GET", "POST"],
)
@administrator_required
def edit_user(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == "POST":

        username = request.form.get(
            "username",
            "",
        ).strip()

        full_name = request.form.get(
            "full_name",
            "",
        ).strip()

        role = request.form.get(
            "role",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        if not username or not full_name:

            flash(
                _("Username and full name are required."),
                "danger",
            )

            return redirect(
                url_for("main.edit_user", user_id=user.id)
            )

        if role not in get_role_names():

            flash(
                _("Invalid role."),
                "danger",
            )

            return redirect(
                url_for("main.edit_user", user_id=user.id)
            )

        existing = User.query.filter_by(
            username=username
        ).first()

        if existing and existing.id != user.id:

            flash(
                _("Username is already in use."),
                "danger",
            )

            return redirect(
                url_for("main.edit_user", user_id=user.id)
            )

        if password and len(password) < MIN_PASSWORD_LENGTH:

            flash(
                _("Password must be at least %(min_length)s characters.")
                % {"min_length": MIN_PASSWORD_LENGTH},
                "danger",
            )

            return redirect(
                url_for("main.edit_user", user_id=user.id)
            )

        user.username = username
        user.full_name = full_name
        user.role = role
        user.is_active = (
            request.form.get("is_active") == "1"
        )

        if password:
            user.set_password(password)

        db.session.commit()

        log_action(
            "update",
            "User",
            entity_label=user.username,
        )

        flash(
            _("User updated successfully."),
            "success",
        )

        return redirect(
            url_for("main.users")
        )

    return render_template(
        "master/user/edit.html",
        user=user,
        role_choices=get_role_names(),
    )


@main.route(
    "/users/<int:user_id>/delete",
    methods=["POST"],
)
@administrator_required
def delete_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:

        flash(
            _("You cannot delete your own account."),
            "danger",
        )

        return redirect(
            url_for("main.users")
        )

    deleted_username = user.username

    db.session.delete(user)
    db.session.commit()

    log_action(
        "delete",
        "User",
        entity_label=deleted_username,
    )

    flash(
        _("User deleted successfully."),
        "success",
    )

    return redirect(
        url_for("main.users")
    )

# ============================================================
# MENU MANAGEMENT (ADMINISTRATOR ONLY)
# ============================================================


