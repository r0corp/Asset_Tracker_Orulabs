"""
CRUD asset, import/export, label & QR cetak.
"""

import io
import os
import uuid

from datetime import datetime, date

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_file,
)
from werkzeug.utils import secure_filename
from flask_babel import gettext as _

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.worksheet.page import PageMargins

from .. import db
from ..models import (
    Asset,
    Category,
    Location,
    Department,
    Vendor,
    AssetMovement,
    WarrantyHistory,
)
from ..auth import requires_permission

from . import main, ASSET_LIST_PER_PAGE
from .helpers import (
    parse_date,
    get_master_data,
    get_warranty_status,
    save_asset_photo,
    delete_asset_photo,
    generate_asset_qr,
    log_action,
)

@main.route("/assets")
@requires_permission("asset", "read")
def assets():

    search = request.args.get(
        "search",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        ""
    ).strip()

    selected_category = request.args.get(
        "category",
        ""
    ).strip()

    selected_location = request.args.get(
        "location",
        ""
    ).strip()

    selected_department = request.args.get(
        "department",
        ""
    ).strip()

    selected_vendor = request.args.get(
        "vendor",
        ""
    ).strip()

    query = Asset.query

    if search:

        search_pattern = f"%{search}%"

        query = query.filter(
            db.or_(
                Asset.asset_tag.ilike(search_pattern),
                Asset.asset_name.ilike(search_pattern),
                Asset.brand.ilike(search_pattern),
                Asset.model.ilike(search_pattern),
                Asset.serial_number.ilike(search_pattern),
                Asset.pic.ilike(search_pattern),
                Asset.vendor.ilike(search_pattern),
            )
        )

    if selected_status:
        query = query.filter(
            Asset.status == selected_status
        )

    if selected_category:
        query = query.filter(
            Asset.category == selected_category
        )

    if selected_location:
        query = query.filter(
            Asset.location == selected_location
        )

    if selected_department:
        query = query.filter(
            Asset.department == selected_department
        )

    if selected_vendor:
        query = query.filter(
            Asset.vendor == selected_vendor
        )

    page = request.args.get(
        "page",
        1,
        type=int,
    )

    pagination = query.order_by(
        Asset.id.desc()
    ).paginate(
        page=page,
        per_page=ASSET_LIST_PER_PAGE,
        error_out=False,
    )

    asset_list = pagination.items

    categories = (
        Category.query
        .order_by(Category.name.asc())
        .all()
    )

    locations = (
        Location.query
        .order_by(Location.name.asc())
        .all()
    )

    departments = (
        Department.query
        .order_by(Department.name.asc())
        .all()
    )

    vendors = (
        Vendor.query
        .order_by(Vendor.name.asc())
        .all()
    )

    return render_template(
        "asset/list.html",
        assets=asset_list,
        pagination=pagination,
        categories=categories,
        locations=locations,
        departments=departments,
        vendors=vendors,
        search=search,
        selected_status=selected_status,
        selected_category=selected_category,
        selected_location=selected_location,
        selected_department=selected_department,
        selected_vendor=selected_vendor,
    )

# ============================================================
# EXPORT ASSET
# ============================================================


@main.route("/assets/export")
@requires_permission("asset", "read")
def export_assets():

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment

    search = request.args.get(
        "search",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        ""
    ).strip()

    selected_category = request.args.get(
        "category",
        ""
    ).strip()

    selected_location = request.args.get(
        "location",
        ""
    ).strip()

    selected_department = request.args.get(
        "department",
        ""
    ).strip()

    selected_vendor = request.args.get(
        "vendor",
        ""
    ).strip()

    query = Asset.query

    if search:

        search_pattern = f"%{search}%"

        query = query.filter(
            db.or_(
                Asset.asset_tag.ilike(search_pattern),
                Asset.asset_name.ilike(search_pattern),
                Asset.brand.ilike(search_pattern),
                Asset.model.ilike(search_pattern),
                Asset.serial_number.ilike(search_pattern),
                Asset.pic.ilike(search_pattern),
                Asset.vendor.ilike(search_pattern),
            )
        )

    if selected_status:
        query = query.filter(
            Asset.status == selected_status
        )

    if selected_category:
        query = query.filter(
            Asset.category == selected_category
        )

    if selected_location:
        query = query.filter(
            Asset.location == selected_location
        )

    if selected_department:
        query = query.filter(
            Asset.department == selected_department
        )

    if selected_vendor:
        query = query.filter(
            Asset.vendor == selected_vendor
        )

    assets = (
        query
        .order_by(Asset.id.desc())
        .all()
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Assets"

    headers = [
        "No",
        "Asset Tag",
        "Asset Name",
        "Category",
        "Brand",
        "Model",
        "Serial Number",
        "Location",
        "Department",
        "PIC",
        "Purchase Date",
        "Purchase Price",
        "Status",
        "Vendor",
        "Warranty",
        "Description",
    ]

    worksheet.append(headers)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    for number, asset in enumerate(
        assets,
        start=1,
    ):

        worksheet.append([
            number,
            asset.asset_tag or "",
            asset.asset_name or "",
            asset.category or "",
            asset.brand or "",
            asset.model or "",
            asset.serial_number or "",
            asset.location or "",
            asset.department or "",
            asset.pic or "",
            asset.purchase_date or "",
            asset.purchase_price or 0,
            asset.status or "",
            asset.vendor or "",
            asset.warranty or "",
            asset.description or "",
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    column_widths = {
        "A": 8,
        "B": 18,
        "C": 30,
        "D": 20,
        "E": 20,
        "F": 20,
        "G": 25,
        "H": 25,
        "I": 25,
        "J": 20,
        "K": 15,
        "L": 18,
        "M": 15,
        "N": 25,
        "O": 20,
        "P": 40,
    }

    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    output = io.BytesIO()

    workbook.save(output)
    output.seek(0)

    filename = (
        "asset_export_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".xlsx"
    )

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

# ============================================================
# EXPORT SEMUA MUTASI ASSET
# ============================================================


@main.route(
    "/assets/import",
    methods=["GET", "POST"],
)
@requires_permission("asset", "create")
def import_assets():

    from openpyxl import load_workbook

    if request.method == "GET":

        return render_template(
            "asset/import.html"
        )

    uploaded_file = request.files.get("file")

    if not uploaded_file:

        flash(
            _("Excel file has not been selected."),
            "danger",
        )

        return render_template(
            "asset/import.html"
        )

    filename = uploaded_file.filename or ""

    if not filename.lower().endswith(
        (".xlsx", ".xlsm")
    ):

        flash(
            _("File format must be .xlsx or .xlsm."),
            "danger",
        )

        return render_template(
            "asset/import.html"
        )

    success_count = 0
    error_count = 0
    errors = []

    try:

        workbook = load_workbook(
            uploaded_file,
            data_only=True,
        )

        worksheet = workbook.active

        rows = list(
            worksheet.iter_rows(
                values_only=True
            )
        )

        if not rows:

            flash(
                _("Excel file is empty."),
                "danger",
            )

            return render_template(
                "asset/import.html"
            )

        headers = [
            str(value).strip()
            if value is not None
            else ""
            for value in rows[0]
        ]

        required_headers = [
            "Asset Tag",
            "Asset Name",
        ]

        missing_headers = [
            header
            for header in required_headers
            if header not in headers
        ]

        if missing_headers:

            flash(
                _("Required columns not found: %(columns)s")
                % {"columns": ", ".join(missing_headers)},
                "danger",
            )

            return render_template(
                "asset/import.html"
            )

        header_map = {
            header: index
            for index, header in enumerate(headers)
            if header
        }

        existing_tags = {
            asset.asset_tag
            for asset in Asset.query.with_entities(
                Asset.asset_tag
            ).all()
            if asset.asset_tag
        }

        imported_tags = set()

        def get_value(row, column):

            index = header_map.get(column)

            if index is None:
                return None

            if index >= len(row):
                return None

            return row[index]

        def clean_text(value):

            if value is None:
                return ""

            return str(value).strip()

        for row_number, row in enumerate(
            rows[1:],
            start=2,
        ):

            try:

                asset_tag = clean_text(
                    get_value(
                        row,
                        "Asset Tag",
                    )
                )

                asset_name = clean_text(
                    get_value(
                        row,
                        "Asset Name",
                    )
                )

                if not asset_tag:
                    raise ValueError(
                        "Asset Tag wajib diisi."
                    )

                if not asset_name:
                    raise ValueError(
                        "Asset Name wajib diisi."
                    )

                if asset_tag in existing_tags:
                    raise ValueError(
                        f"Asset Tag '{asset_tag}' "
                        "sudah ada di database."
                    )

                if asset_tag in imported_tags:
                    raise ValueError(
                        f"Asset Tag '{asset_tag}' "
                        "duplikat di file Excel."
                    )

                purchase_date = get_value(
                    row,
                    "Purchase Date",
                )

                if purchase_date:

                    if isinstance(
                        purchase_date,
                        datetime,
                    ):

                        purchase_date = (
                            purchase_date.date()
                        )

                    elif not isinstance(
                        purchase_date,
                        date,
                    ):

                        purchase_date = parse_date(
                            str(purchase_date).strip()
                        )

                purchase_price = get_value(
                    row,
                    "Purchase Price",
                )

                if purchase_price in (
                    None,
                    "",
                ):

                    purchase_price = 0

                try:

                    purchase_price = float(
                        purchase_price
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    raise ValueError(
                        "Purchase Price harus berupa angka."
                    )

                status = clean_text(
                    get_value(
                        row,
                        "Status",
                    )
                )

                if not status:
                    status = "Active"

                asset = Asset(
                    asset_tag=asset_tag,
                    asset_name=asset_name,
                    category=clean_text(
                        get_value(row, "Category")
                    ),
                    brand=clean_text(
                        get_value(row, "Brand")
                    ),
                    model=clean_text(
                        get_value(row, "Model")
                    ),
                    serial_number=clean_text(
                        get_value(row, "Serial Number")
                    ),
                    location=clean_text(
                        get_value(row, "Location")
                    ),
                    department=clean_text(
                        get_value(row, "Department")
                    ),
                    pic=clean_text(
                        get_value(row, "PIC")
                    ),
                    vendor=clean_text(
                        get_value(row, "Vendor")
                    ),
                    warranty=clean_text(
                        get_value(row, "Warranty")
                    ),
                    purchase_date=purchase_date,
                    purchase_price=purchase_price,
                    status=status,
                    description=clean_text(
                        get_value(row, "Description")
                    ),
                )

                db.session.add(asset)

                imported_tags.add(asset_tag)

                success_count += 1

            except Exception as exc:

                error_count += 1

                errors.append(
                    f"Baris {row_number}: {exc}"
                )

        if success_count > 0:

            try:

                db.session.commit()

            except Exception as exc:

                db.session.rollback()

                success_count = 0

                error_count = max(
                    len(rows) - 1,
                    0,
                )

                errors = [
                    "Gagal menyimpan data ke database: "
                    + str(exc)
                ]

        else:

            db.session.rollback()

    except Exception as exc:

        success_count = 0

        error_count = max(
            len(rows) - 1,
            0,
        ) if "rows" in locals() else 0

        errors.append(
            "Gagal membaca file Excel: "
            + str(exc)
        )

    return render_template(
        "asset/import_result.html",
        success_count=success_count,
        error_count=error_count,
        errors=errors,
    )

# ============================================================
# DOWNLOAD TEMPLATE IMPORT
# ============================================================


@main.route("/assets/import/template")
@requires_permission("asset", "read")
def download_import_template():

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "Assets"

    headers = [
        "Asset Tag",
        "Asset Name",
        "Category",
        "Brand",
        "Model",
        "Serial Number",
        "Location",
        "Department",
        "PIC",
        "Vendor",
        "Warranty",
        "Purchase Date",
        "Purchase Price",
        "Status",
        "Description",
    ]

    worksheet.append(headers)

    for cell in worksheet[1]:

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    worksheet.freeze_panes = "A2"

    widths = {
        "A": 18,
        "B": 30,
        "C": 20,
        "D": 20,
        "E": 20,
        "F": 25,
        "G": 25,
        "H": 25,
        "I": 20,
        "J": 25,
        "K": 20,
        "L": 15,
        "M": 18,
        "N": 15,
        "O": 40,
    }

    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width

    output = io.BytesIO()

    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="asset_import_template.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

# ============================================================
# ASSET LABELS
# ============================================================


@main.route("/assets/labels")
@requires_permission("asset", "read")
def asset_labels():

    assets = (
        Asset.query
        .order_by(Asset.asset_tag.asc())
        .all()
    )

    return render_template(
        "asset/labels_select.html",
        assets=assets,
    )

# ============================================================
# PRINT ASSET LABELS
# ============================================================


@main.route("/assets/labels/print")
@requires_permission("asset", "read")
def print_asset_labels():

    selected_ids = request.args.getlist("ids")

    if not selected_ids:

        flash(
            _("Select at least one asset to print."),
            "warning",
        )

        return redirect(
            url_for("main.asset_labels")
        )

    valid_ids = []

    for value in selected_ids:

        try:

            valid_ids.append(
                int(value)
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

    if not valid_ids:

        flash(
            _("Selected assets are invalid."),
            "danger",
        )

        return redirect(
            url_for("main.asset_labels")
        )

    assets = (
        Asset.query
        .filter(
            Asset.id.in_(valid_ids)
        )
        .order_by(
            Asset.asset_tag.asc()
        )
        .all()
    )

    if not assets:

        flash(
            _("Selected assets were not found."),
            "danger",
        )

        return redirect(
            url_for("main.asset_labels")
        )

    # Pastikan QR setiap asset tersedia
    qr_folder = os.path.join(
        current_app.static_folder,
        "qrcodes",
    )

    os.makedirs(
        qr_folder,
        exist_ok=True,
    )

    for asset in assets:

        qr_filename = f"{asset.asset_tag}.png"

        qr_path = os.path.join(
            qr_folder,
            qr_filename,
        )

        if not os.path.exists(qr_path):

            try:

                generate_asset_qr(asset)

            except Exception as exc:

                current_app.logger.error(
                    "QR generation error for %s: %s",
                    asset.asset_tag,
                    exc,
                )

    return render_template(
        "asset/labels.html",
        assets=assets,
    )

# ============================================================
# DELETE ASSET
# ============================================================


@main.route(
    "/assets/<int:asset_id>/delete",
    methods=["POST"],
)
@requires_permission("asset", "delete")
def delete_asset(asset_id):

    asset = Asset.query.get_or_404(
        asset_id
    )

    # Hapus QR Code asset
    qr_filename = f"{asset.asset_tag}.png"

    qr_path = os.path.join(
        current_app.static_folder,
        "qrcodes",
        qr_filename,
    )

    if os.path.exists(qr_path):

        try:
            os.remove(qr_path)
        except OSError:
            pass

    deleted_asset_tag = asset.asset_tag

    db.session.delete(asset)
    db.session.commit()

    log_action(
        "delete",
        "Asset",
        entity_label=deleted_asset_tag,
    )

    flash(
        _("Asset was successfully deleted."),
        "success",
    )

    return redirect(
        url_for("main.assets")
    )

# ============================================================
# ADD ASSET
# ============================================================


@main.route(
    "/assets/add",
    methods=["GET", "POST"],
)
@requires_permission("asset", "create")
def add_asset():

    (
        categories,
        locations,
        departments,
        vendors,
    ) = get_master_data()

    if request.method == "POST":

        # ====================================================
        # DATA DASAR
        # ====================================================

        asset_tag = request.form.get(
            "asset_tag",
            "",
        ).strip()

        asset_name = request.form.get(
            "asset_name",
            "",
        ).strip()

        # ====================================================
        # VALIDASI ASSET TAG
        # ====================================================

        if not asset_tag:

            flash(
                _("Asset Tag is required."),
                "danger",
            )

            return render_template(
                "asset/add.html",
                categories=categories,
                locations=locations,
                departments=departments,
                vendors=vendors,
            )

        # ====================================================
        # VALIDASI NAMA ASSET
        # ====================================================

        if not asset_name:

            flash(
                _("Asset name is required."),
                "danger",
            )

            return render_template(
                "asset/add.html",
                categories=categories,
                locations=locations,
                departments=departments,
                vendors=vendors,
            )

        # ====================================================
        # CEK DUPLIKAT ASSET TAG
        # ====================================================

        existing = Asset.query.filter_by(
            asset_tag=asset_tag
        ).first()

        if existing:

            flash(
                _("Asset Tag is already in use."),
                "danger",
            )

            return render_template(
                "asset/add.html",
                categories=categories,
                locations=locations,
                departments=departments,
                vendors=vendors,
            )

        # ====================================================
        # PURCHASE PRICE
        # ====================================================

        purchase_price = request.form.get(
            "purchase_price",
            "",
        ).strip()

        try:

            purchase_price = (
                float(purchase_price)
                if purchase_price
                else None
            )

        except (ValueError, TypeError):

            purchase_price = None

        # ====================================================
        # FOTO ASSET
        # ====================================================

        photo_file = request.files.get(
            "photo"
        )

        photo_filename = None

        if photo_file and photo_file.filename:

            try:

                photo_filename = save_asset_photo(
                    photo_file,
                    asset_tag,
                )

            except ValueError as exc:

                flash(
                    _("Invalid asset photo: %(error)s")
                    % {"error": str(exc)},
                    "danger",
                )

                return render_template(
                    "asset/add.html",
                    categories=categories,
                    locations=locations,
                    departments=departments,
                    vendors=vendors,
                )

            except Exception as exc:

                current_app.logger.error(
                    "Asset photo upload error: %s",
                    exc,
                )

                flash(
                    _("Asset photo failed to upload."),
                    "danger",
                )

                return render_template(
                    "asset/add.html",
                    categories=categories,
                    locations=locations,
                    departments=departments,
                    vendors=vendors,
                )

        # ====================================================
        # BUAT OBJECT ASSET
        # ====================================================

        asset = Asset(

            asset_tag=asset_tag,

            asset_name=asset_name,

            photo=photo_filename,

            category=request.form.get(
                "category"
            ),

            brand=request.form.get(
                "brand"
            ),

            model=request.form.get(
                "model"
            ),

            serial_number=request.form.get(
                "serial_number"
            ),

            location=request.form.get(
                "location"
            ),

            department=request.form.get(
                "department"
            ),

            pic=request.form.get(
                "pic"
            ),

            purchase_date=parse_date(
                request.form.get(
                    "purchase_date"
                )
            ),

            purchase_price=purchase_price,

            vendor=request.form.get(
                "vendor"
            ),

            warranty=request.form.get(
                "warranty"
            ),

            status=request.form.get(
                "status"
            ) or "Active",

            description=request.form.get(
                "description"
            ),
        )

        # ====================================================
        # SIMPAN DATABASE
        # ====================================================

        try:

            db.session.add(
                asset
            )

            db.session.commit()

            log_action(
                "create",
                "Asset",
                entity_label=asset.asset_tag,
            )

        except Exception as exc:

            db.session.rollback()

            # Jika database gagal disimpan,
            # hapus foto yang sudah terlanjur diupload.

            if photo_filename:

                delete_asset_photo(
                    photo_filename
                )

            current_app.logger.error(
                "Asset save error: %s",
                exc,
            )

            flash(
                _("Asset failed to save."),
                "danger",
            )

            return render_template(
                "asset/add.html",
                categories=categories,
                locations=locations,
                departments=departments,
                vendors=vendors,
            )

        # ====================================================
        # GENERATE QR CODE
        # ====================================================

        try:

            generate_asset_qr(
                asset
            )

        except Exception as exc:

            current_app.logger.error(
                "QR generation error: %s",
                exc,
            )

        # ====================================================
        # SUCCESS
        # ====================================================

        flash(
            _("Asset was successfully added."),
            "success",
        )

        return redirect(
            url_for(
                "main.asset_detail",
                asset_id=asset.id,
            )
        )

    # ========================================================
    # GET REQUEST
    # ========================================================

    return render_template(
        "asset/add.html",
        categories=categories,
        locations=locations,
        departments=departments,
        vendors=vendors,
    )

# ============================================================
# ASSET DETAIL
# ============================================================


@main.route("/assets/<int:asset_id>")
@requires_permission("asset", "read")
def asset_detail(asset_id):

    asset = Asset.query.get_or_404(
        asset_id
    )

    movements = (
        AssetMovement.query
        .filter_by(asset_id=asset.id)
        .order_by(
            AssetMovement.movement_date.desc(),
            AssetMovement.id.desc(),
        )
        .all()
    )

    qr_filename = f"{asset.asset_tag}.png"

    qr_path = os.path.join(
        current_app.static_folder,
        "qrcodes",
        qr_filename,
    )

    if not os.path.exists(qr_path):

        try:

            generate_asset_qr(asset)

        except Exception as exc:

            current_app.logger.error(
                "QR generation error: %s",
                exc,
            )

    return render_template(
        "asset/detail.html",
        asset=asset,
        movements=movements,
        qr_filename=qr_filename,
    )

# ============================================================
# EDIT ASSET
# ============================================================


@main.route(
    "/assets/edit/<int:asset_id>",
    methods=["GET", "POST"]
)
@requires_permission("asset", "edit")
def edit_asset(asset_id):

    asset = Asset.query.get_or_404(
        asset_id
    )

    # --------------------------------------------------------
    # SIMPAN DATA WARRANTY LAMA
    # SEBELUM ASSET DIUBAH
    # --------------------------------------------------------

    old_purchase_date = asset.purchase_date

    old_warranty = (
        asset.warranty
        or ""
    ).strip()

    old_warranty_info = get_warranty_status(
        old_purchase_date,
        old_warranty,
        today=date.today(),
    )

    old_end_date = old_warranty_info.get(
        "end_date"
    )

    # --------------------------------------------------------
    # FOLDER UPLOAD FOTO
    # --------------------------------------------------------

    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads",
        "assets",
    )

    os.makedirs(
        upload_folder,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        categories = (
            Category.query
            .order_by(
                Category.name.asc()
            )
            .all()
        )

        locations = (
            Location.query
            .order_by(
                Location.name.asc()
            )
            .all()
        )

        departments = (
            Department.query
            .order_by(
                Department.name.asc()
            )
            .all()
        )

        vendors = (
            Vendor.query
            .order_by(
                Vendor.name.asc()
            )
            .all()
        )

        return render_template(
            "asset/edit.html",
            asset=asset,
            categories=categories,
            locations=locations,
            departments=departments,
            vendors=vendors,
        )

    # ========================================================
    # POST
    # ========================================================

    # --------------------------------------------------------
    # ASSET TAG
    # --------------------------------------------------------

    asset.asset_tag = (
        request.form.get(
            "asset_tag",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # ASSET NAME
    # --------------------------------------------------------

    asset.asset_name = (
        request.form.get(
            "asset_name",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    asset.category = (
        request.form.get(
            "category",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    asset.brand = (
        request.form.get(
            "brand",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    asset.model = (
        request.form.get(
            "model",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # SERIAL NUMBER
    # --------------------------------------------------------

    asset.serial_number = (
        request.form.get(
            "serial_number",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    asset.location = (
        request.form.get(
            "location",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # DEPARTMENT
    # --------------------------------------------------------

    asset.department = (
        request.form.get(
            "department",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # PIC
    # --------------------------------------------------------

    asset.pic = (
        request.form.get(
            "pic",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # VENDOR
    # --------------------------------------------------------

    asset.vendor = (
        request.form.get(
            "vendor",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # WARRANTY BARU
    # --------------------------------------------------------

    new_warranty = (
        request.form.get(
            "warranty",
            ""
        ).strip()
    )

    asset.warranty = new_warranty

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    asset.status = (
        request.form.get(
            "status",
            ""
        ).strip()
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    asset.description = (
        request.form.get(
            "description",
            ""
        ).strip()
    )

    # ========================================================
    # PURCHASE DATE
    # ========================================================

    purchase_date_value = (
        request.form.get(
            "purchase_date",
            ""
        ).strip()
    )

    if purchase_date_value:

        try:

            asset.purchase_date = parse_date(
                purchase_date_value
            )

        except Exception:

            flash(
                _("Invalid purchase date format."),
                "danger",
            )

            return redirect(
                url_for(
                    "main.edit_asset",
                    asset_id=asset.id,
                )
            )

    else:

        asset.purchase_date = None

    # ========================================================
    # PURCHASE PRICE
    # ========================================================

    purchase_price_value = (
        request.form.get(
            "purchase_price",
            ""
        ).strip()
    )

    if purchase_price_value:

        try:

            asset.purchase_price = float(
                purchase_price_value
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                _("Invalid purchase price."),
                "danger",
            )

            return redirect(
                url_for(
                    "main.edit_asset",
                    asset_id=asset.id,
                )
            )

    else:

        asset.purchase_price = 0

    # ========================================================
    # DELETE PHOTO
    # ========================================================

    delete_photo = (
        request.form.get(
            "delete_photo"
        )
        == "1"
    )

    if delete_photo:

        if asset.photo:

            old_photo_path = os.path.join(
                upload_folder,
                asset.photo,
            )

            if os.path.isfile(
                old_photo_path
            ):

                try:

                    os.remove(
                        old_photo_path
                    )

                except OSError:

                    current_app.logger.warning(
                        "Gagal menghapus foto lama: %s",
                        old_photo_path,
                    )

        asset.photo = None

    # ========================================================
    # NEW PHOTO
    # ========================================================

    photo = request.files.get(
        "photo"
    )

    if photo and photo.filename:

        allowed_extensions = {
            "jpg",
            "jpeg",
            "png",
            "webp",
        }

        original_filename = (
            secure_filename(
                photo.filename
            )
        )

        extension = ""

        if "." in original_filename:

            extension = (
                original_filename
                .rsplit(".", 1)[1]
                .lower()
            )

        if extension not in allowed_extensions:

            flash(
                _(
                    "Unsupported photo format. "
                    "Use JPG, JPEG, PNG, or WEBP."
                ),
                "danger",
            )

            return redirect(
                url_for(
                    "main.edit_asset",
                    asset_id=asset.id,
                )
            )

        # ----------------------------------------------------
        # HAPUS FOTO LAMA
        # ----------------------------------------------------

        if asset.photo:

            old_photo_path = os.path.join(
                upload_folder,
                asset.photo,
            )

            if os.path.isfile(
                old_photo_path
            ):

                try:

                    os.remove(
                        old_photo_path
                    )

                except OSError:

                    current_app.logger.warning(
                        "Gagal menghapus foto lama: %s",
                        old_photo_path,
                    )

        # ----------------------------------------------------
        # NAMA FILE BARU
        # ----------------------------------------------------

        new_filename = (
            f"{asset.asset_tag}_"
            f"{uuid.uuid4().hex[:10]}."
            f"{extension}"
        )

        new_filename = secure_filename(
            new_filename
        )

        photo_path = os.path.join(
            upload_folder,
            new_filename,
        )

        photo.save(
            photo_path
        )

        asset.photo = new_filename

    # ========================================================
    # WARRANTY HISTORY
    # ========================================================

    warranty_changed = (
        old_warranty != (
            asset.warranty
            or ""
        ).strip()
        or old_purchase_date != asset.purchase_date
    )

    if warranty_changed:

        new_warranty_info = get_warranty_status(
            asset.purchase_date,
            asset.warranty,
            today=date.today(),
        )

        new_end_date = (
            new_warranty_info.get(
                "end_date"
            )
        )

        warranty_history = WarrantyHistory(

            asset_id=asset.id,

            old_warranty=old_warranty,

            old_end_date=old_end_date,

            new_warranty=(
                asset.warranty
                or ""
            ).strip(),

            new_end_date=new_end_date,

            changed_date=date.today(),

            reason=(
                "Perubahan warranty "
                "melalui Edit Asset"
            ),

            notes=(
                "Warranty diperbarui "
                "melalui halaman Edit Asset."
            ),
        )

        db.session.add(
            warranty_history
        )

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    try:

        db.session.commit()

        log_action(
            "update",
            "Asset",
            entity_label=asset.asset_tag,
        )

        # ----------------------------------------------------
        # PESAN BERHASIL
        # ----------------------------------------------------

        if warranty_changed:

            flash(
                _(
                    "Asset was successfully updated "
                    "and warranty history was recorded."
                ),
                "success",
            )

        else:

            flash(
                _("Asset was successfully updated."),
                "success",
            )

        return redirect(
            url_for(
                "main.asset_detail",
                asset_id=asset.id,
            )
        )

    except Exception as exc:

        db.session.rollback()

        current_app.logger.exception(
            "Gagal memperbarui asset: %s",
            exc,
        )

        flash(
            _("Failed to update asset."),
            "danger",
        )

        return redirect(
            url_for(
                "main.edit_asset",
                asset_id=asset.id,
            )
        )

# ============================================================
# ASSET MOVEMENTS
# ============================================================

# ============================================================
# ASSET MOVEMENT HISTORY
# ============================================================


@main.route(
    "/assets/labels/excel",
    methods=["POST"],
)
@requires_permission("asset", "read")
def export_asset_labels_excel():

    # ========================================================
    # IMPORT
    # ========================================================

    import io
    import os

    from openpyxl import Workbook

    from openpyxl.drawing.image import (
        Image as ExcelImage,
    )

    from openpyxl.styles import (
        Font,
        Alignment,
        Border,
        Side,
        PatternFill,
    )

    from openpyxl.worksheet.page import (
        PageMargins,
    )

    from openpyxl.utils import (
        get_column_letter,
    )

    # ========================================================
    # AMBIL ID ASSET
    # ========================================================

    selected_ids = request.form.getlist(
        "ids"
    )

    # ========================================================
    # FALLBACK
    # ========================================================

    if not selected_ids:

        selected_ids = request.form.getlist(
            "asset_ids"
        )

    # ========================================================
    # VALIDASI
    # ========================================================

    if not selected_ids:

        flash(
            _("Select at least one asset to export to Excel."),
            "warning",
        )

        return redirect(
            url_for(
                "main.asset_labels"
            )
        )

    # ========================================================
    # KONVERSI ID
    # ========================================================

    valid_ids = []

    for value in selected_ids:

        try:

            asset_id = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        if asset_id not in valid_ids:

            valid_ids.append(
                asset_id
            )

    # ========================================================
    # VALIDASI ID
    # ========================================================

    if not valid_ids:

        flash(
            _("Invalid asset ID."),
            "danger",
        )

        return redirect(
            url_for(
                "main.asset_labels"
            )
        )

    # ========================================================
    # AMBIL DATA ASSET
    #
    # URUTAN SAMA DENGAN LABEL
    # ========================================================

    assets = (
        Asset.query
        .filter(
            Asset.id.in_(valid_ids)
        )
        .order_by(
            Asset.id.desc()
        )
        .all()
    )

    # ========================================================
    # JIKA KOSONG
    # ========================================================

    if not assets:

        flash(
            _("Selected assets were not found."),
            "danger",
        )

        return redirect(
            url_for(
                "main.asset_labels"
            )
        )

    # ========================================================
    # PERUSAHAAN
    # ========================================================

    company_name = (
        "PT TRADECORP INDONESIA"
    )

    # ========================================================
    # FOLDER QR
    # ========================================================

    qr_folder = os.path.join(
        current_app.static_folder,
        "qrcodes",
    )

    # ========================================================
    # 1 ASSET = 5 LABEL
    # ========================================================

    repeated_assets = []

    for asset in assets:

        for _ in range(5):

            repeated_assets.append(
                asset
            )

    # ========================================================
    # KONFIGURASI TOM & JERRY 108
    # ========================================================

    LABEL_WIDTH_MM = 38.0

    LABEL_HEIGHT_MM = 18.0

    COLUMNS = 5

    ROWS = 8

    LABELS_PER_SHEET = (
        COLUMNS * ROWS
    )

    # ========================================================
    # A4
    # ========================================================

    A4_WIDTH_MM = 210.0

    A4_HEIGHT_MM = 297.0

    # ========================================================
    # POSISI LABEL
    #
    # Mengikuti layout HTML terakhir:
    #
    # column-gap = 2.5 mm
    # row-gap    = 0 mm
    # padding-top = 5 mm
    #
    # Total lebar:
    #
    # 5 x 38 = 190
    # 4 x 2.5 = 10
    #
    # TOTAL = 200 MM
    #
    # A4 = 210 MM
    #
    # SISA = 10 MM
    #
    # LEFT = 5 MM
    # RIGHT = 5 MM
    # ========================================================

    COLUMN_GAP_MM = 2.5

    ROW_GAP_MM = 0.0

    TOP_MARGIN_MM = 5.0

    TOTAL_LABEL_WIDTH_MM = (

        (
            COLUMNS
            * LABEL_WIDTH_MM
        )

        +

        (
            (COLUMNS - 1)
            * COLUMN_GAP_MM
        )

    )

    LEFT_MARGIN_MM = (

        A4_WIDTH_MM
        - TOTAL_LABEL_WIDTH_MM

    ) / 2

    RIGHT_MARGIN_MM = (
        LEFT_MARGIN_MM
    )

    # ========================================================
    # KONVERSI MM KE POINT
    # ========================================================

    def mm_to_points(
        mm
    ):

        return (
            mm
            * 72
            / 25.4
        )

    # ========================================================
    # KONVERSI MM KE PIXEL
    # ========================================================

    def mm_to_pixels(
        mm
    ):

        return int(
            round(
                mm
                * 96
                / 25.4
            )
        )

    # ========================================================
    # KONVERSI MM KE EXCEL COLUMN WIDTH
    #
    # Excel tidak menggunakan MM secara langsung.
    #
    # Nilai ini merupakan pendekatan yang stabil untuk
    # kebutuhan print.
    # ========================================================

    def mm_to_excel_width(
        mm
    ):

        pixels = (
            mm_to_pixels(
                mm
            )
        )

        return max(
            0.1,
            (
                pixels - 5
            ) / 7,
        )

    # ========================================================
    # UKURAN INTERNAL LABEL
    #
    # INFO KIRI
    # QR KANAN
    # ========================================================

    INFO_WIDTH_MM = 25.0

    INTERNAL_GAP_MM = 1.2

    QR_WIDTH_MM = 10.5

    # ========================================================
    # JUMLAH SHEET
    # ========================================================

    total_labels = len(
        repeated_assets
    )

    total_sheets = (

        (
            total_labels
            + LABELS_PER_SHEET
            - 1
        )
        // LABELS_PER_SHEET

    )

    # ========================================================
    # WORKBOOK
    # ========================================================

    workbook = Workbook()

    # ========================================================
    # HAPUS DEFAULT NANTI JIKA PERLU
    # ========================================================

    default_sheet = (
        workbook.active
    )

    # ========================================================
    # BORDER
    # ========================================================

    thin_side = Side(
        style="thin",
        color="555555",
    )

    no_side = Side(
        style=None,
    )

    # ========================================================
    # FILL
    # ========================================================

    white_fill = PatternFill(
        fill_type="solid",
        fgColor="FFFFFF",
    )

    # ========================================================
    # LOOP SHEET
    # ========================================================

    for sheet_index in range(
        total_sheets
    ):

        # ====================================================
        # SHEET
        # ====================================================

        if sheet_index == 0:

            worksheet = (
                default_sheet
            )

            worksheet.title = (
                "Label 1"
            )

        else:

            worksheet = (
                workbook.create_sheet(
                    title=(
                        "Label "
                        + str(
                            sheet_index + 1
                        )
                    )
                )
            )

        # ====================================================
        # GRIDLINES
        # ====================================================

        worksheet.sheet_view.showGridLines = False

        # ====================================================
        # PRINT CONFIG
        # ====================================================

        worksheet.page_setup.orientation = (
            "portrait"
        )

        worksheet.page_setup.paperSize = (
            worksheet.PAPERSIZE_A4
        )

        # ====================================================
        # SANGAT PENTING
        #
        # JANGAN FIT TO PAGE
        #
        # AGAR UKURAN LABEL TIDAK BERUBAH.
        # ====================================================

        worksheet.sheet_properties.pageSetUpPr.fitToPage = False

        worksheet.page_setup.fitToWidth = None

        worksheet.page_setup.fitToHeight = None

        # ====================================================
        # SCALE
        #
        # 100%
        # ====================================================

        worksheet.page_setup.scale = 100

        # ====================================================
        # MARGIN
        #
        # OPENPYXL MENGGUNAKAN INCH.
        # ====================================================

        worksheet.page_margins = PageMargins(

            left=(
                LEFT_MARGIN_MM
                / 25.4
            ),

            right=(
                RIGHT_MARGIN_MM
                / 25.4
            ),

            top=(
                TOP_MARGIN_MM
                / 25.4
            ),

            bottom=(
                0
                / 25.4
            ),

            header=0,

            footer=0,

        )

        # ====================================================
        # CENTER HORIZONTAL
        # ====================================================

        worksheet.print_options.horizontalCentered = False

        worksheet.print_options.verticalCentered = False

        # ====================================================
        # GRID
        #
        # Setiap label menggunakan 3 kolom:
        #
        # INFO | GAP | QR
        #
        # kemudian 1 kolom gap antar label.
        # ====================================================

        COLUMNS_PER_LABEL = 4

        # ====================================================
        # SET COLUMN WIDTH
        # ====================================================

        for label_column in range(
            COLUMNS
        ):

            base = (
                label_column
                * COLUMNS_PER_LABEL
            )

            # ------------------------------------------------
            # INFO
            # ------------------------------------------------

            info_col = (
                base + 1
            )

            worksheet.column_dimensions[
                get_column_letter(
                    info_col
                )
            ].width = (
                mm_to_excel_width(
                    INFO_WIDTH_MM
                )
            )

            # ------------------------------------------------
            # INTERNAL GAP
            # ------------------------------------------------

            internal_gap_col = (
                base + 2
            )

            worksheet.column_dimensions[
                get_column_letter(
                    internal_gap_col
                )
            ].width = (
                mm_to_excel_width(
                    INTERNAL_GAP_MM
                )
            )

            # ------------------------------------------------
            # QR
            # ------------------------------------------------

            qr_col = (
                base + 3
            )

            worksheet.column_dimensions[
                get_column_letter(
                    qr_col
                )
            ].width = (
                mm_to_excel_width(
                    QR_WIDTH_MM
                )
            )

            # ------------------------------------------------
            # GAP ANTAR LABEL
            # ------------------------------------------------

            external_gap_col = (
                base + 4
            )

            worksheet.column_dimensions[
                get_column_letter(
                    external_gap_col
                )
            ].width = (
                mm_to_excel_width(
                    COLUMN_GAP_MM
                )
            )

        # ====================================================
        # BARIS
        #
        # 4 BARIS INTERNAL / LABEL
        #
        # 8 LABEL VERTIKAL
        #
        # TOTAL 32 BARIS.
        #
        # Setiap label tetap 18 mm.
        # ====================================================

        INTERNAL_ROWS = 4

        INTERNAL_ROW_HEIGHT_MM = (

            LABEL_HEIGHT_MM
            / INTERNAL_ROWS

        )

        TOTAL_ROWS = (
            ROWS
            * INTERNAL_ROWS
        )

        for row in range(
            1,
            TOTAL_ROWS + 1,
        ):

            worksheet.row_dimensions[
                row
            ].height = (
                mm_to_points(
                    INTERNAL_ROW_HEIGHT_MM
                )
            )

        # ====================================================
        # DATA UNTUK SHEET
        # ====================================================

        sheet_start = (

            sheet_index
            * LABELS_PER_SHEET

        )

        sheet_end = min(

            sheet_start
            + LABELS_PER_SHEET,

            total_labels,

        )

        sheet_assets = (

            repeated_assets[
                sheet_start:
                sheet_end
            ]

        )

        # ====================================================
        # LOOP LABEL
        # ====================================================

        for label_index, asset in enumerate(
            sheet_assets
        ):

            # =================================================
            # POSISI LABEL
            # =================================================

            label_row = (

                label_index
                // COLUMNS

            )

            label_column = (

                label_index
                % COLUMNS

            )

            # =================================================
            # BASE COLUMN
            # =================================================

            base_column = (

                label_column
                * COLUMNS_PER_LABEL

            )

            info_column = (
                base_column + 1
            )

            internal_gap_column = (
                base_column + 2
            )

            qr_column = (
                base_column + 3
            )

            external_gap_column = (
                base_column + 4
            )

            # =================================================
            # BASE ROW
            # =================================================

            base_row = (

                label_row
                * INTERNAL_ROWS

            ) + 1

            # =================================================
            # DATA
            # =================================================

            asset_tag = str(
                asset.asset_tag
                or "-"
            )

            asset_name = str(
                asset.asset_name
                or "-"
            )

            serial_number = str(
                asset.serial_number
                or "-"
            )

            # =================================================
            # TEKS LABEL
            # =================================================

            label_lines = [

                {
                    "text":
                        company_name,

                    "size":
                        5.2,

                    "bold":
                        True,
                },

                {
                    "text":
                        asset_tag,

                    "size":
                        6.5,

                    "bold":
                        True,
                },

                {
                    "text":
                        asset_name,

                    "size":
                        5.2,

                    "bold":
                        True,
                },

                {
                    "text":
                        "S/N: "
                        + serial_number,

                    "size":
                        4.8,

                    "bold":
                        False,
                },

            ]

            # =================================================
            # 4 BARIS INTERNAL
            # =================================================

            for line_index, line_data in enumerate(
                label_lines
            ):

                row = (
                    base_row
                    + line_index
                )

                # =============================================
                # INFO
                # =============================================

                info_cell = worksheet.cell(

                    row=row,

                    column=info_column,

                )

                info_cell.value = (
                    line_data["text"]
                )

                info_cell.font = Font(

                    name="Arial",

                    size=line_data["size"],

                    bold=line_data["bold"],

                )

                info_cell.alignment = Alignment(

                    horizontal="left",

                    vertical="center",

                    wrap_text=False,

                    shrink_to_fit=True,

                )

                info_cell.fill = (
                    white_fill
                )

                # =============================================
                # BORDER INFO
                # =============================================

                info_cell.border = Border(

                    left=thin_side,

                    right=no_side,

                    top=(
                        thin_side
                        if line_index == 0
                        else no_side
                    ),

                    bottom=(
                        thin_side
                        if line_index == 3
                        else no_side
                    ),

                )

                # =============================================
                # INTERNAL GAP
                # =============================================

                gap_cell = worksheet.cell(

                    row=row,

                    column=internal_gap_column,

                )

                gap_cell.value = None

                gap_cell.fill = (
                    white_fill
                )

                gap_cell.border = Border(

                    left=no_side,

                    right=no_side,

                    top=(
                        thin_side
                        if line_index == 0
                        else no_side
                    ),

                    bottom=(
                        thin_side
                        if line_index == 3
                        else no_side
                    ),

                )

                # =============================================
                # QR AREA
                # =============================================

                qr_cell = worksheet.cell(

                    row=row,

                    column=qr_column,

                )

                qr_cell.fill = (
                    white_fill
                )

                qr_cell.border = Border(

                    left=no_side,

                    right=thin_side,

                    top=(
                        thin_side
                        if line_index == 0
                        else no_side
                    ),

                    bottom=(
                        thin_side
                        if line_index == 3
                        else no_side
                    ),

                )

                # =============================================
                # EXTERNAL GAP
                # =============================================

                external_gap_cell = (
                    worksheet.cell(
                        row=row,
                        column=external_gap_column,
                    )
                )

                external_gap_cell.value = None

                external_gap_cell.fill = (
                    white_fill
                )

        # ====================================================
        # QR CODE
        # ====================================================

        for label_index, asset in enumerate(
            sheet_assets
        ):

            # =================================================
            # POSISI
            # =================================================

            label_row = (

                label_index
                // COLUMNS

            )

            label_column = (

                label_index
                % COLUMNS

            )

            # =================================================
            # COLUMN QR
            # =================================================

            base_column = (

                label_column
                * COLUMNS_PER_LABEL

            )

            qr_column = (
                base_column + 3
            )

            qr_letter = (
                get_column_letter(
                    qr_column
                )
            )

            # =================================================
            # ROW
            # =================================================

            base_row = (

                label_row
                * INTERNAL_ROWS
            ) + 1

            # =================================================
            # QR FILE
            # =================================================

            qr_filename = (

                str(
                    asset.asset_tag
                    or ""
                )
                + ".png"

            )

            qr_path = os.path.join(

                qr_folder,

                qr_filename,

            )

            # =================================================
            # CEK FILE
            # =================================================

            if not os.path.isfile(
                qr_path
            ):

                current_app.logger.warning(

                    "QR tidak ditemukan: %s",

                    qr_path,

                )

                continue

            # =================================================
            # MASUKKAN QR
            # =================================================

            try:

                qr_image = ExcelImage(
                    qr_path
                )

                # =============================================
                # 10.5 x 10.5 MM
                # =============================================

                qr_size = mm_to_pixels(
                    10.5
                )

                qr_image.width = (
                    qr_size
                )

                qr_image.height = (
                    qr_size
                )

                # =============================================
                # ANCHOR
                # =============================================

                qr_image.anchor = (

                    f"{qr_letter}"
                    f"{base_row}"

                )

                worksheet.add_image(
                    qr_image
                )

            except Exception as exc:

                current_app.logger.exception(

                    "Gagal memasukkan QR "
                    "asset %s ke Excel: %s",

                    asset.asset_tag,

                    exc,

                )

        # ====================================================
        # PRINT AREA
        # ====================================================

        last_column = (

            COLUMNS
            * COLUMNS_PER_LABEL

        )

        last_column_letter = (
            get_column_letter(
                last_column
            )
        )

        worksheet.print_area = (

            f"A1:"
            f"{last_column_letter}"
            f"{TOTAL_ROWS}"

        )

        # ====================================================
        # PRINT TITLES
        # ====================================================

        worksheet.print_title_rows = None

        # ====================================================
        # PAGE BREAK
        # ====================================================

        worksheet.sheet_properties.pageSetUpPr.autoPageBreaks = False

        # ====================================================
        # HEADER / FOOTER
        # ====================================================

        worksheet.oddHeader.center.text = ""

        worksheet.oddFooter.center.text = ""

        # ====================================================
        # PRINT GRIDLINES
        # ====================================================

        worksheet.print_options.gridLines = False

    # ========================================================
    # SIMPAN EXCEL
    # ========================================================

    output = io.BytesIO()

    workbook.save(
        output
    )

    output.seek(0)

    # ========================================================
    # NAMA FILE
    # ========================================================

    filename = (

        "Cetak_QR_Label_Asset_"

        "Tom_Jerry_108_"

        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        + ".xlsx"

    )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    return send_file(

        output,

        as_attachment=True,

        download_name=filename,

        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),

    )
