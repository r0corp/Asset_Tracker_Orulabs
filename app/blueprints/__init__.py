"""
Semua route aplikasi didaftarkan pada SATU objek Blueprint ("main")
yang sama, dipecah ke banyak file per domain (assets, movements,
warranty, master_data, company, users, menus, login, overview).

Ini sengaja dibuat begini (bukan satu Blueprint terpisah per domain)
supaya endpoint tetap bernama "main.xxx" persis seperti sebelumnya -
sehingga seluruh url_for("main.xxx") di template TIDAK perlu diubah
sama sekali.
"""

from datetime import datetime

from flask import (
    Blueprint,
    redirect,
    request,
    url_for,
)
from flask_login import current_user

from .. import db


main = Blueprint("main", __name__)

ASSET_LIST_PER_PAGE = 25
MOVEMENT_LIST_PER_PAGE = 25


class SimplePagination:
    """
    Pagination in-memory untuk list yang sudah difilter/dihitung
    di Python (bukan langsung dari query SQL), misalnya movement
    global yang status CURRENT/HISTORY-nya dihitung lintas seluruh
    data sebelum dipotong per halaman.
    """

    def __init__(self, items_all, page, per_page):

        self.per_page = per_page
        self.total = len(items_all)
        self.pages = max(
            1,
            (self.total + per_page - 1) // per_page,
        )
        self.page = min(max(page, 1), self.pages)

        start = (self.page - 1) * per_page

        self.items = items_all[start:start + per_page]

        self.has_prev = self.page > 1
        self.has_next = self.page < self.pages
        self.prev_num = self.page - 1
        self.next_num = self.page + 1

    def iter_pages(
        self,
        left_edge=1,
        right_edge=1,
        left_current=2,
        right_current=2,
    ):

        last = 0

        for num in range(1, self.pages + 1):

            if (
                num <= left_edge
                or (
                    num > self.page - left_current - 1
                    and num < self.page + right_current
                )
                or num > self.pages - right_edge
            ):

                if last + 1 != num:
                    yield None

                yield num

                last = num

# ============================================================
# LOGIN GATE
# ============================================================

PUBLIC_ENDPOINTS = {
    "main.login",
    "main.verify_asset_movement",
    "main.set_language",
}


@main.before_request
def require_login():

    if request.endpoint in PUBLIC_ENDPOINTS:
        return None

    if not current_user.is_authenticated:

        return redirect(
            url_for(
                "main.login",
                next=request.path,
            )
        )

    return None


# ============================================================
# JEJAK AKTIVITAS USER (status online)
# ============================================================
# Diperbarui paling sering tiap 60 detik per user (bukan di setiap
# request) supaya tidak membebani database dengan UPDATE terus-
# menerus. "Online" dihitung dari selisih last_seen ini - lihat
# User.is_online di models.py.

LAST_SEEN_UPDATE_INTERVAL_SECONDS = 60


@main.before_request
def touch_last_seen():

    if not current_user.is_authenticated:
        return None

    now = datetime.utcnow()

    if (
        not current_user.last_seen
        or (now - current_user.last_seen).total_seconds()
        > LAST_SEEN_UPDATE_INTERVAL_SECONDS
    ):

        current_user.last_seen = now
        db.session.commit()

    return None


# ============================================================
# IMPORT SEMUA MODUL ROUTE (supaya @main.route ter-register)
# ============================================================

from . import helpers  # noqa: E402,F401
from . import login  # noqa: E402,F401
from . import language  # noqa: E402,F401
from . import profile  # noqa: E402,F401
from . import users  # noqa: E402,F401
from . import roles  # noqa: E402,F401
from . import menus  # noqa: E402,F401
from . import overview  # noqa: E402,F401
from . import warranty  # noqa: E402,F401
from . import assets  # noqa: E402,F401
from . import movements  # noqa: E402,F401
from . import master_data  # noqa: E402,F401
from . import company  # noqa: E402,F401
from . import app_settings  # noqa: E402,F401
from . import audit  # noqa: E402,F401
from . import backup  # noqa: E402,F401
from . import cache  # noqa: E402,F401
