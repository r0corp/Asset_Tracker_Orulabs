"""
Manajemen menu navigasi dinamis - khusus administrator.
"""

from flask import render_template, request, redirect, url_for, flash
from flask_babel import gettext as _

from .. import db
from ..models import MenuItem, Role
from ..auth import administrator_required

from . import main
from .helpers import log_action


def get_role_names():

    return [
        role.name
        for role in Role.query.order_by(Role.name.asc()).all()
    ]


def _menu_roles_from_form():

    selected = request.form.getlist("roles")

    valid_names = get_role_names()

    selected = [
        role
        for role in selected
        if role in valid_names
    ]

    return (
        ",".join(selected)
        if selected
        else None
    )


@main.route("/menus")
@administrator_required
def menus():

    top_items = (
        MenuItem.query
        .filter_by(parent_id=None)
        .order_by(
            MenuItem.order,
            MenuItem.id,
        )
        .all()
    )

    return render_template(
        "master/menu/list.html",
        top_items=top_items,
    )


@main.route(
    "/menus/add",
    methods=["GET", "POST"],
)
@administrator_required
def add_menu():

    parent_choices = (
        MenuItem.query
        .filter_by(parent_id=None)
        .order_by(
            MenuItem.order,
            MenuItem.id,
        )
        .all()
    )

    if request.method == "POST":

        label = request.form.get(
            "label",
            "",
        ).strip()

        icon = request.form.get(
            "icon",
            "",
        ).strip()

        url = request.form.get(
            "url",
            "",
        ).strip()

        order = request.form.get(
            "order",
            "0",
        ).strip()

        parent_id = request.form.get(
            "parent_id",
            "",
        ).strip()

        is_divider = (
            request.form.get("is_divider") == "1"
        )

        if not label and not is_divider:

            flash(
                _("Menu label is required."),
                "danger",
            )

            return redirect(
                url_for("main.add_menu")
            )

        try:
            order = int(order) if order else 0
        except ValueError:
            order = 0

        menu_item = MenuItem(
            label=label or "Pemisah",
            icon=icon or None,
            url=(url or None) if not is_divider else None,
            order=order,
            parent_id=(
                int(parent_id)
                if parent_id
                else None
            ),
            roles=_menu_roles_from_form(),
            is_active=(
                request.form.get("is_active") == "1"
            ),
            is_divider=is_divider,
        )

        db.session.add(menu_item)
        db.session.commit()

        log_action(
            "create",
            "MenuItem",
            entity_label=menu_item.label,
        )

        flash(
            _("Menu added successfully."),
            "success",
        )

        return redirect(
            url_for("main.menus")
        )

    return render_template(
        "master/menu/add.html",
        parent_choices=parent_choices,
        role_choices=get_role_names(),
    )


@main.route(
    "/menus/<int:menu_id>/edit",
    methods=["GET", "POST"],
)
@administrator_required
def edit_menu(menu_id):

    menu_item = MenuItem.query.get_or_404(menu_id)

    parent_choices = (
        MenuItem.query
        .filter(
            MenuItem.parent_id.is_(None),
            MenuItem.id != menu_item.id,
        )
        .order_by(
            MenuItem.order,
            MenuItem.id,
        )
        .all()
    )

    if request.method == "POST":

        label = request.form.get(
            "label",
            "",
        ).strip()

        icon = request.form.get(
            "icon",
            "",
        ).strip()

        url = request.form.get(
            "url",
            "",
        ).strip()

        order = request.form.get(
            "order",
            "0",
        ).strip()

        parent_id = request.form.get(
            "parent_id",
            "",
        ).strip()

        is_divider = (
            request.form.get("is_divider") == "1"
        )

        if not label and not is_divider:

            flash(
                _("Menu label is required."),
                "danger",
            )

            return redirect(
                url_for("main.edit_menu", menu_id=menu_item.id)
            )

        try:
            order = int(order) if order else 0
        except ValueError:
            order = 0

        menu_item.label = label or "Pemisah"
        menu_item.icon = icon or None
        menu_item.url = (url or None) if not is_divider else None
        menu_item.order = order
        menu_item.parent_id = (
            int(parent_id)
            if parent_id
            else None
        )
        menu_item.roles = _menu_roles_from_form()
        menu_item.is_active = (
            request.form.get("is_active") == "1"
        )
        menu_item.is_divider = is_divider

        db.session.commit()

        log_action(
            "update",
            "MenuItem",
            entity_label=menu_item.label,
        )

        flash(
            _("Menu updated successfully."),
            "success",
        )

        return redirect(
            url_for("main.menus")
        )

    return render_template(
        "master/menu/edit.html",
        menu_item=menu_item,
        parent_choices=parent_choices,
        role_choices=get_role_names(),
    )


@main.route(
    "/menus/<int:menu_id>/delete",
    methods=["POST"],
)
@administrator_required
def delete_menu(menu_id):

    menu_item = MenuItem.query.get_or_404(menu_id)

    deleted_label = menu_item.label

    db.session.delete(menu_item)
    db.session.commit()

    log_action(
        "delete",
        "MenuItem",
        entity_label=deleted_label,
    )

    flash(
        _("Menu deleted successfully."),
        "success",
    )

    return redirect(
        url_for("main.menus")
    )

# ============================================================
# HELPER - PARSE DATE
# ============================================================


