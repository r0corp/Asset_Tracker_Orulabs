"""
Backup & Restore database - administrator only.

Backup berupa file .zip berisi instance/asset.db (database) dan
seluruh isi app/static/uploads (foto asset, logo company). File
QR code tidak diikutkan karena bisa di-generate ulang otomatis
dari data asset/movement.

Restore MENIMPA database yang sedang berjalan - operasi ini
sengaja dibuat berlapis pengamanannya:
1. Wajib ketik "RESTORE" untuk konfirmasi.
2. Sebelum menimpa, otomatis membuat backup kondisi SAAT INI dulu
   (jadi kalau restore-nya keliru, masih bisa balik lagi).
3. Setelah restore, user dipaksa logout (data user bisa saja
   berbeda di backup lama).
"""

import io
import os
import shutil
import zipfile

from datetime import datetime

from flask import (
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
)
from flask_babel import gettext as _
from flask_login import logout_user
from werkzeug.utils import secure_filename

from .. import db
from ..auth import administrator_required

from . import main
from .helpers import log_action


DB_ENTRY_NAME = "instance/asset.db"

SQLITE_MAGIC = b"SQLite format 3\x00"


def get_backup_folder():

    folder = current_app.config.get("BACKUP_FOLDER")

    if not folder:

        folder = os.path.join(
            current_app.root_path,
            "..",
            "backups",
        )

    folder = os.path.abspath(folder)

    os.makedirs(folder, exist_ok=True)

    return folder


def get_db_path():
    """
    Path file database SQLite yang SEDANG DIPAKAI aplikasi saat ini
    (dibaca dari config, bukan ditebak dari lokasi folder). Supaya
    saat dites (DATABASE_URL diarahkan ke file sementara), backup
    & restore tidak pernah menyentuh instance/asset.db yang asli.
    """

    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    prefix = "sqlite:///"

    if not uri.startswith(prefix):

        raise RuntimeError(
            "Backup/restore cuma didukung untuk database SQLite."
        )

    return uri[len(prefix):]


def get_uploads_folder():

    return os.path.join(
        current_app.static_folder,
        "uploads",
    )


def create_backup_zip(prefix="backup"):
    """
    Membuat file .zip backup (database + uploads) di folder backups/
    dan mengembalikan nama filenya.
    """

    db_path = get_db_path()

    if not os.path.exists(db_path):
        raise FileNotFoundError("File database tidak ditemukan.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    zip_filename = f"{prefix}_{timestamp}.zip"

    zip_path = os.path.join(
        get_backup_folder(),
        zip_filename,
    )

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:

        zf.write(db_path, DB_ENTRY_NAME)

        uploads_folder = get_uploads_folder()

        if os.path.isdir(uploads_folder):

            for root, dirs, files in os.walk(uploads_folder):

                for fname in files:

                    full_path = os.path.join(root, fname)

                    rel_path = os.path.relpath(
                        full_path,
                        os.path.dirname(uploads_folder),
                    )

                    zf.write(
                        full_path,
                        os.path.join("static", rel_path),
                    )

    return zip_filename


def validate_backup_zip(zip_path):
    """
    Memastikan file .zip yang mau dipakai restore benar-benar
    backup yang valid (ada instance/asset.db dan formatnya SQLite
    asli), supaya tidak menimpa database dengan file sembarangan.
    """

    if not zipfile.is_zipfile(zip_path):
        return "File bukan .zip yang valid."

    with zipfile.ZipFile(zip_path) as zf:

        if DB_ENTRY_NAME not in zf.namelist():
            return (
                f"File .zip ini tidak berisi '{DB_ENTRY_NAME}' - "
                "bukan hasil backup dari halaman ini."
            )

        header = zf.read(DB_ENTRY_NAME)[:16]

        if header != SQLITE_MAGIC:
            return "File database di dalam .zip rusak/bukan format SQLite."

    return None


def perform_restore(zip_path):
    """
    Menimpa database + uploads yang sedang berjalan dengan isi
    file .zip backup. Mengembalikan (True, None) kalau berhasil,
    atau (False, pesan_error) kalau gagal.
    """

    error = validate_backup_zip(zip_path)

    if error:
        return False, error

    db_path = get_db_path()

    uploads_folder = get_uploads_folder()

    # Tutup semua koneksi database yang sedang terbuka, supaya
    # file asset.db bisa ditimpa dengan aman.
    db.session.remove()
    db.engine.dispose()

    try:

        with zipfile.ZipFile(zip_path) as zf:

            # ----------------------------------------------------
            # DATABASE
            # ----------------------------------------------------

            with zf.open(DB_ENTRY_NAME) as source, open(db_path, "wb") as target:
                shutil.copyfileobj(source, target)

            # ----------------------------------------------------
            # UPLOADS (foto asset, logo company)
            # ----------------------------------------------------

            static_root = os.path.dirname(uploads_folder)

            for entry in zf.namelist():

                if not entry.startswith("static/uploads/"):
                    continue

                if entry.endswith("/"):
                    continue

                dest_path = os.path.join(
                    static_root,
                    entry[len("static/"):].replace("/", os.sep),
                )

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                with zf.open(entry) as source, open(dest_path, "wb") as target:
                    shutil.copyfileobj(source, target)

    except OSError as exc:

        return False, (
            "Gagal menulis file saat restore "
            f"({exc}). Coba lagi, atau restart aplikasi lalu coba lagi."
        )

    # Pastikan koneksi berikutnya membaca file yang baru saja ditimpa.
    db.engine.dispose()

    return True, None


@main.route("/backup")
@administrator_required
def backup_list():

    folder = get_backup_folder()

    files = []

    for fname in sorted(os.listdir(folder), reverse=True):

        full_path = os.path.join(folder, fname)

        if not os.path.isfile(full_path):
            continue

        files.append({
            "name": fname,
            "size_mb": round(
                os.path.getsize(full_path) / (1024 * 1024),
                2,
            ),
            "created_at": datetime.fromtimestamp(
                os.path.getmtime(full_path)
            ),
        })

    return render_template(
        "backup/list.html",
        files=files,
    )


@main.route(
    "/backup/create",
    methods=["POST"],
)
@administrator_required
def backup_create():

    try:

        zip_filename = create_backup_zip()

    except FileNotFoundError as exc:

        flash(
            _("Failed to create backup. Detail: %(error)s") % {"error": str(exc)},
            "danger",
        )

        return redirect(
            url_for("main.backup_list")
        )

    log_action(
        "create",
        "Backup",
        entity_label=zip_filename,
    )

    flash(
        _("Backup created successfully: %(filename)s") % {"filename": zip_filename},
        "success",
    )

    return redirect(
        url_for("main.backup_list")
    )


@main.route("/backup/download/<path:filename>")
@administrator_required
def backup_download(filename):

    safe_name = secure_filename(filename)

    folder = get_backup_folder()

    full_path = os.path.join(folder, safe_name)

    if not os.path.isfile(full_path):

        flash(
            _("Backup file not found."),
            "danger",
        )

        return redirect(
            url_for("main.backup_list")
        )

    return send_file(
        full_path,
        as_attachment=True,
        download_name=safe_name,
    )


@main.route(
    "/backup/delete/<path:filename>",
    methods=["POST"],
)
@administrator_required
def backup_delete(filename):

    safe_name = secure_filename(filename)

    folder = get_backup_folder()

    full_path = os.path.join(folder, safe_name)

    if os.path.isfile(full_path):

        try:

            os.remove(full_path)

            flash(
                _("Backup deleted successfully."),
                "success",
            )

        except OSError:

            flash(
                _("The backup file is being used by another process. Please try again shortly."),
                "warning",
            )

    return redirect(
        url_for("main.backup_list")
    )


# ============================================================
# RESTORE
# ============================================================


@main.route(
    "/backup/restore/<path:filename>",
    methods=["POST"],
)
@administrator_required
def backup_restore(filename):

    confirm_text = request.form.get(
        "confirm_text",
        "",
    ).strip()

    if confirm_text != "RESTORE":

        flash(
            _('Type "RESTORE" (all uppercase) to confirm.'),
            "danger",
        )

        return redirect(
            url_for("main.backup_list")
        )

    safe_name = secure_filename(filename)

    zip_path = os.path.join(
        get_backup_folder(),
        safe_name,
    )

    if not os.path.isfile(zip_path):

        flash(
            _("Backup file not found."),
            "danger",
        )

        return redirect(
            url_for("main.backup_list")
        )

    # Jaring pengaman: backup kondisi SEKARANG dulu sebelum ditimpa.
    try:
        safety_backup = create_backup_zip(prefix="before_restore")
    except FileNotFoundError:
        safety_backup = None

    success, error = perform_restore(zip_path)

    if not success:

        flash(
            _("Restore failed: %(error)s") % {"error": error},
            "danger",
        )

        return redirect(
            url_for("main.backup_list")
        )

    log_action(
        "update",
        "Backup",
        entity_label=safe_name,
        description=(
            "Restore database"
            + (
                f" (backup pengaman: {safety_backup})"
                if safety_backup
                else ""
            )
        ),
    )

    flash(
        _(
            "Restore successful. You will be logged out automatically - "
            "please log in again. If the app behaves oddly afterward, "
            "restart it."
        ),
        "success",
    )

    logout_user()

    return redirect(
        url_for("main.login")
    )


@main.route(
    "/backup/restore-upload",
    methods=["GET", "POST"],
)
@administrator_required
def backup_restore_upload():

    if request.method == "POST":

        confirm_text = request.form.get(
            "confirm_text",
            "",
        ).strip()

        if confirm_text != "RESTORE":

            flash(
                _('Type "RESTORE" (all uppercase) to confirm.'),
                "danger",
            )

            return redirect(
                url_for("main.backup_restore_upload")
            )

        upload = request.files.get("file")

        if not upload or not upload.filename:

            flash(
                _("Please select a .zip backup file first."),
                "danger",
            )

            return redirect(
                url_for("main.backup_restore_upload")
            )

        # Simpan sementara untuk divalidasi & dipakai restore.
        temp_path = os.path.join(
            get_backup_folder(),
            "_uploaded_" + secure_filename(upload.filename),
        )

        upload.save(temp_path)

        try:

            safety_backup = create_backup_zip(prefix="before_restore")
        except FileNotFoundError:
            safety_backup = None

        success, error = perform_restore(temp_path)

        os.remove(temp_path)

        if not success:

            flash(
                _("Restore failed: %(error)s") % {"error": error},
                "danger",
            )

            return redirect(
                url_for("main.backup_restore_upload")
            )

        log_action(
            "update",
            "Backup",
            entity_label=upload.filename,
            description=(
                "Restore database dari file upload"
                + (
                    f" (backup pengaman: {safety_backup})"
                    if safety_backup
                    else ""
                )
            ),
        )

        flash(
            _(
                "Restore successful. You will be logged out automatically - "
                "please log in again. If the app behaves oddly afterward, "
                "restart it."
            ),
            "success",
        )

        logout_user()

        return redirect(
            url_for("main.login")
        )

    return render_template("backup/restore_upload.html")
