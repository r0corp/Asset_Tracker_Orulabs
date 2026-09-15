"""
Route login dan logout.
"""

from flask import render_template, request, redirect, url_for, flash
from flask_babel import gettext as _

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from .. import limiter
from ..models import User

from . import main

@main.route(
    "/login",
    methods=["GET", "POST"],
)
@limiter.limit(
    "10 per minute",
    methods=["POST"],
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("main.dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(
            username=username
        ).first()

        if (
            user
            and user.is_active
            and user.check_password(password)
        ):

            login_user(user, remember=remember)

            next_url = request.form.get("next")

            return redirect(
                next_url
                or url_for("main.dashboard")
            )

        flash(
            _("Incorrect username or password."),
            "danger",
        )

    return render_template(
        "login.html",
        next=request.args.get("next", ""),
    )


@main.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        _("You have been logged out."),
        "info",
    )

    return redirect(
        url_for("main.login")
    )

