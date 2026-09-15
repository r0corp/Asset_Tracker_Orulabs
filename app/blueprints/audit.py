"""
Halaman lihat audit log (riwayat siapa mengubah/menghapus apa) -
khusus administrator.
"""

from flask import render_template, request

from ..models import AuditLog
from ..auth import administrator_required

from . import main, ASSET_LIST_PER_PAGE


@main.route("/audit-log")
@administrator_required
def audit_log():

    page = request.args.get(
        "page",
        1,
        type=int,
    )

    pagination = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .paginate(
            page=page,
            per_page=ASSET_LIST_PER_PAGE,
            error_out=False,
        )
    )

    return render_template(
        "audit/list.html",
        pagination=pagination,
    )
