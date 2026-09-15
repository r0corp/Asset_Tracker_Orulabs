"""
Pengaturan branding aplikasi: nama aplikasi, footer, pesan
halaman login, logo (lebar & kotak) - administrator only.

Beda dengan Company (blueprints/company.py) yang isinya data
BISNIS perusahaan untuk kop dokumen. Ini murni soal tampilan
aplikasi itu sendiri.
"""

import os

from flask import render_template, request, redirect, url_for, flash, current_app
from flask_babel import gettext as _

from .. import db
from ..models import AppSetting
from ..auth import administrator_required

from . import main
from .helpers import log_action


ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}

BRAND_DISPLAY_MODES = {"logo_only", "name_only", "logo_and_name"}


def get_app_setting():

    setting = AppSetting.query.order_by(AppSetting.id.asc()).first()

    if not setting:

        setting = AppSetting(
            app_name="Asset Tracker",
        )

        db.session.add(setting)
        db.session.commit()

    return setting


def get_branding_upload_folder():

    folder = current_app.config.get("BRANDING_UPLOAD_FOLDER")

    if not folder:

        folder = os.path.join(
            current_app.static_folder,
            "uploads",
            "branding",
        )

    os.makedirs(folder, exist_ok=True)

    return folder


def save_logo(file_field_name, setting, model_field):
    """
    Simpan file logo yang diupload untuk field tertentu
    (logo_wide / logo_square). Mengembalikan pesan error
    (string) kalau format tidak valid, atau None kalau
    berhasil/tidak ada file baru.
    """

    logo_file = request.files.get(file_field_name)

    if not logo_file or not logo_file.filename:
        return None

    extension = os.path.splitext(logo_file.filename)[1].lower()

    if extension not in ALLOWED_LOGO_EXTENSIONS:

        return (
            _("Logo format must be PNG, JPG, JPEG, WEBP, or SVG.")
        )

    upload_folder = get_branding_upload_folder()

    old_filename = getattr(setting, model_field)

    if old_filename:

        old_path = os.path.join(upload_folder, old_filename)

        if os.path.exists(old_path):

            try:
                os.remove(old_path)
            except OSError:
                pass

    new_filename = f"{model_field}{extension}"

    logo_file.save(os.path.join(upload_folder, new_filename))

    setattr(setting, model_field, new_filename)

    return None


@main.route(
    "/settings/general",
    methods=["GET", "POST"],
)
@administrator_required
def app_settings_general():

    setting = get_app_setting()

    if request.method == "POST":

        app_name = request.form.get(
            "app_name",
            "",
        ).strip()

        footer_text = request.form.get(
            "footer_text",
            "",
        ).strip()

        login_message = request.form.get(
            "login_message",
            "",
        ).strip()

        brand_display_mode = request.form.get(
            "brand_display_mode",
            "logo_only",
        ).strip()

        if brand_display_mode not in BRAND_DISPLAY_MODES:
            brand_display_mode = "logo_only"

        if not app_name:

            flash(
                _("Application name is required."),
                "danger",
            )

            return redirect(
                url_for("main.app_settings_general")
            )

        error = save_logo("logo_wide", setting, "logo_wide")

        if error:

            flash(error, "danger")

            return redirect(
                url_for("main.app_settings_general")
            )

        error = save_logo("logo_square", setting, "logo_square")

        if error:

            flash(error, "danger")

            return redirect(
                url_for("main.app_settings_general")
            )

        if request.form.get("remove_logo_wide") == "1":

            if setting.logo_wide:

                old_path = os.path.join(
                    get_branding_upload_folder(),
                    setting.logo_wide,
                )

                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            setting.logo_wide = None

        if request.form.get("remove_logo_square") == "1":

            if setting.logo_square:

                old_path = os.path.join(
                    get_branding_upload_folder(),
                    setting.logo_square,
                )

                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            setting.logo_square = None

        setting.app_name = app_name
        setting.footer_text = footer_text or None
        setting.login_message = login_message or None
        setting.brand_display_mode = brand_display_mode

        db.session.commit()

        log_action(
            "update",
            "AppSetting",
            entity_label=setting.app_name,
        )

        flash(
            _("Application settings saved successfully."),
            "success",
        )

        return redirect(
            url_for("main.app_settings_general")
        )

    return render_template(
        "settings/general.html",
        setting=setting,
    )
