"""
Halaman profil akun milik user yang sedang login
(lihat detail akun, ganti nama & password sendiri).
"""

from flask import render_template, request, redirect, url_for, flash
from flask_babel import gettext as _
from flask_login import login_required, current_user

from .. import db

from . import main
from .helpers import log_action

MIN_PASSWORD_LENGTH = 8


@main.route(
    "/profile",
    methods=["GET", "POST"],
)
@login_required
def profile():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        password_confirm = request.form.get(
            "password_confirm",
            "",
        )

        if not full_name:

            flash(
                _("Full name is required."),
                "danger",
            )

            return redirect(
                url_for("main.profile")
            )

        if password and password != password_confirm:

            flash(
                _("New password confirmation does not match."),
                "danger",
            )

            return redirect(
                url_for("main.profile")
            )

        if password and len(password) < MIN_PASSWORD_LENGTH:

            flash(
                _(
                    "Password must be at least %(min_length)s characters.",
                    min_length=MIN_PASSWORD_LENGTH,
                ),
                "danger",
            )

            return redirect(
                url_for("main.profile")
            )

        current_user.full_name = full_name

        password_changed = bool(password)

        if password:
            current_user.set_password(password)

        db.session.commit()

        log_action(
            "update",
            "User",
            entity_label=current_user.username,
            description=(
                "Ganti password sendiri"
                if password_changed
                else "Update profil sendiri"
            ),
        )

        flash(
            _("Profile updated successfully."),
            "success",
        )

        return redirect(
            url_for("main.profile")
        )

    return render_template("profile.html")
