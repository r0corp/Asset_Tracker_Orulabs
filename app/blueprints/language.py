"""
Ganti bahasa aplikasi (disimpan di session, per-browser).
Tidak butuh login - bisa diganti dari halaman login juga.
"""

from flask import current_app, redirect, request, session, url_for

from . import main


@main.route("/language/<lang_code>")
def set_language(lang_code):

    if lang_code in current_app.config["LANGUAGES"]:
        session["language"] = lang_code

    return redirect(
        request.referrer
        or url_for("main.dashboard")
    )
