import os
from datetime import timedelta

from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))


SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY belum diset. Buat file .env di folder project ini "
        "berisi SECRET_KEY=<hasil generate>, misalnya lewat:\n"
        "  python -c \"import secrets; print(secrets.token_hex(32))\""
    )


class Config:
    SECRET_KEY = SECRET_KEY

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "sqlite:///"
        + os.path.join(BASE_DIR, "instance", "asset.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Batas ukuran upload (foto asset, logo company) - 5 MB.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    RATELIMIT_ENABLED = (
        os.environ.get("RATELIMIT_ENABLED", "True") == "True"
    )

    # ========================================================
    # KEAMANAN SESI
    # ========================================================
    # Umur cookie sesi (server-side idle check-nya ada di
    # blueprints/__init__.py::enforce_session_security, ini cuma
    # lapisan tambahan di sisi cookie - jendelanya "geser" otomatis
    # tiap request selama masih aktif, lihat login() di
    # blueprints/login.py yang men-set session.permanent = True).
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # ========================================================
    # BAHASA (i18n)
    # ========================================================

    BABEL_DEFAULT_LOCALE = "en"

    BABEL_TRANSLATION_DIRECTORIES = os.path.join(
        BASE_DIR,
        "app",
        "translations",
    )

    # Kode bahasa -> (nama tampilan, kode negara bendera ISO 3166-1
    # alpha-2 lowercase, dipakai oleh library flag-icons di base.html
    # sebagai class "fi fi-<kode>" - bukan emoji, supaya bendera tetap
    # tampil sebagai gambar meski OS/browser tidak mendukung emoji
    # bendera, misalnya Windows).
    # Tambah bahasa baru cukup nambah baris di sini + folder
    # terjemahan baru (lihat app/translations/README.md).
    LANGUAGES = {
        "en": ("English", "gb"),
        "id": ("Indonesia", "id"),
    }
