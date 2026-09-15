"""
Halaman utilitas untuk membersihkan cache di sisi browser
(localStorage, sessionStorage, Cache API) - berguna kalau
tampilan terasa "nyangkut"/tidak update setelah ada perubahan.

Tidak berhubungan dengan cache di server (aplikasi ini memang
tidak memakai server-side cache), murni utilitas sisi browser -
aman untuk semua role, dan aman diabaikan kalau tidak diperlukan.
"""

from flask import render_template
from flask_login import login_required

from . import main


@main.route("/clear-cache")
@login_required
def clear_cache():

    return render_template("clear_cache.html")
