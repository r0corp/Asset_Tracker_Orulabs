"""
Profil company (nama, alamat, logo, dsb).
"""

import os

from flask import render_template, request, redirect, url_for, flash, current_app
from flask_babel import gettext as _

from .. import db
from ..models import Company
from ..auth import requires_permission

from . import main
from .helpers import log_action

@main.route("/company")
@requires_permission("company", "read")
def company():

    company = (
        Company.query
        .order_by(Company.id.asc())
        .first()
    )

    return render_template(
        "company/list.html",
        company=company
    )

# ============================================================
# EDIT / SETUP COMPANY
# ============================================================


@main.route(
    "/company/edit",
    methods=["GET", "POST"]
)
@requires_permission("company", "edit")
def edit_company():

    company = (
        Company.query
        .order_by(Company.id.asc())
        .first()
    )

    # ========================================================
    # BUAT DATA COMPANY JIKA BELUM ADA
    # ========================================================

    if not company:

        company = Company(
            name="Nama Perusahaan",
            document_prefix="MT"
        )

        db.session.add(company)
        db.session.commit()

    # ========================================================
    # SIMPAN DATA
    # ========================================================

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        website = request.form.get(
            "website",
            ""
        ).strip()

        tax_number = request.form.get(
            "tax_number",
            ""
        ).strip()

        document_prefix = request.form.get(
            "document_prefix",
            "MT"
        ).strip()

        # ====================================================
        # VALIDASI
        # ====================================================

        if not name:

            flash(
                _("Company name is required."),
                "danger"
            )

            return render_template(
                "company/edit.html",
                company=company
            )

        if not document_prefix:

            document_prefix = "MT"

        # ====================================================
        # UPDATE DATA
        # ====================================================

        company.name = name

        company.address = address

        company.phone = phone

        company.email = email

        company.website = website

        company.tax_number = tax_number

        company.document_prefix = (
            document_prefix.upper()
        )

        # ====================================================
        # UPLOAD LOGO
        # ====================================================

        logo_file = request.files.get(
            "logo"
        )

        if logo_file and logo_file.filename:

            original_filename = (
                logo_file.filename
            )

            extension = os.path.splitext(
                original_filename
            )[1].lower()

            allowed_extensions = {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp"
            }

            if extension not in allowed_extensions:

                flash(
                    _("Logo format must be PNG, JPG, JPEG, or WEBP."),
                    "danger"
                )

                return render_template(
                    "company/edit.html",
                    company=company
                )

            upload_folder = os.path.join(
                current_app.static_folder,
                "uploads",
                "company"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            # ================================================
            # HAPUS LOGO LAMA
            # ================================================

            if company.logo:

                old_logo_path = os.path.join(
                    upload_folder,
                    company.logo
                )

                if os.path.exists(
                    old_logo_path
                ):

                    try:

                        os.remove(
                            old_logo_path
                        )

                    except OSError:

                        pass

            # ================================================
            # NAMA FILE AMAN
            # ================================================

            logo_filename = (
                "company_logo"
                + extension
            )

            logo_path = os.path.join(
                upload_folder,
                logo_filename
            )

            logo_file.save(
                logo_path
            )

            company.logo = logo_filename

        # ====================================================
        # SIMPAN DATABASE
        # ====================================================

        db.session.commit()

        log_action(
            "update",
            "Company",
            entity_label=company.name,
        )

        flash(
            _("Company data updated successfully."),
            "success"
        )

        return redirect(
            url_for(
                "main.company"
            )
        )

    return render_template(
        "company/edit.html",
        company=company
    )

# ============================================================
# EXPORT ASSET LABEL - TOM & JERRY NO. 108
# ============================================================


