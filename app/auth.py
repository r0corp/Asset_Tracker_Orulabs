from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_babel import gettext as _
from flask_login import current_user

from .models import ROLE_ADMINISTRATOR, Role


def roles_required(*roles):

    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(*args, **kwargs):

            if not current_user.is_authenticated:

                return redirect(
                    url_for("main.login")
                )

            if current_user.role not in roles:

                flash(
                    _("You do not have access to this page."),
                    "danger",
                )

                abort(403)

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def administrator_required(view_func):

    return roles_required(ROLE_ADMINISTRATOR)(view_func)


def requires_permission(object_name, action):
    """
    Cek izin dari matrix Role/Permission (Manajemen Role), bukan
    dari nama role yang di-hardcode. Role "administrator" selalu
    lolos (superuser) - supaya tidak pernah ada kondisi di mana
    tidak ada satupun role yang bisa mengelola sistem.

    Untuk role lain, izin ditentukan oleh checkbox Create/Read/Edit/
    Delete yang diatur administrator di halaman Manajemen Role untuk
    role tersebut pada object_name ini. Kalau belum diatur sama
    sekali, default-nya DITOLAK (aman/deny-by-default).
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(*args, **kwargs):

            if not current_user.is_authenticated:

                return redirect(
                    url_for("main.login")
                )

            if current_user.role == ROLE_ADMINISTRATOR:
                return view_func(*args, **kwargs)

            role = Role.query.filter_by(
                name=current_user.role
            ).first()

            permission = (
                role.permission_for(object_name)
                if role
                else None
            )

            allowed = (
                permission.allows(action)
                if permission
                else False
            )

            if not allowed:

                flash(
                    _("You do not have permission to perform this action."),
                    "danger",
                )

                abort(403)

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
