"""
Mutasi asset: daftar, laporan, export, tambah, koreksi, QR verifikasi.
"""

import io
import os

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

from flask_babel import gettext as _

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from .. import db
from ..models import (
    Asset,
    Category,
    Location,
    Department,
    Vendor,
    AssetMovement,
    AssetMovementCorrection,
    Company,
)

from ..auth import requires_permission

from . import main, MOVEMENT_LIST_PER_PAGE, SimplePagination
from .helpers import parse_date, generate_asset_movement_qr

@main.route("/assets/movements/export")
@requires_permission("movement", "read")
def export_asset_movements():

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment

    movements = (
        AssetMovement.query
        .order_by(
            AssetMovement.movement_date.desc(),
            AssetMovement.id.desc(),
        )
        .all()
    )

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "Mutasi Asset"

    headers = [
        "No",
        "No. Mutasi",
        "Tanggal Mutasi",
        "Asset Tag",
        "Nama Asset",
        "Dari Lokasi",
        "Ke Lokasi",
        "Dari Department",
        "Ke Department",
        "Dari PIC",
        "Ke PIC",
        "Alasan",
        "Catatan",
        "Nama Penyerah",
        "Jabatan Penyerah",
        "Nama Penerima",
        "Jabatan Penerima",
        "Dibuat",
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

    for number, movement in enumerate(
        movements,
        start=1,
    ):

        asset = movement.asset

        worksheet.append([
            number,
            movement.movement_no or "",
            (
                movement.movement_date.strftime("%d-%m-%Y")
                if movement.movement_date
                else ""
            ),
            asset.asset_tag if asset else "",
            asset.asset_name if asset else "",
            movement.from_location or "",
            movement.to_location or "",
            movement.from_department or "",
            movement.to_department or "",
            movement.from_pic or "",
            movement.to_pic or "",
            movement.reason or "",
            movement.notes or "",
            movement.from_signer_name or "",
            movement.from_signer_position or "",
            movement.to_signer_name or "",
            movement.to_signer_position or "",
            (
                movement.created_at.strftime("%d-%m-%Y %H:%M")
                if movement.created_at
                else ""
            ),
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    column_widths = {
        "A": 8,
        "B": 22,
        "C": 18,
        "D": 20,
        "E": 30,
        "F": 25,
        "G": 25,
        "H": 25,
        "I": 25,
        "J": 20,
        "K": 20,
        "L": 35,
        "M": 40,
        "N": 25,
        "O": 25,
        "P": 25,
        "Q": 25,
        "R": 22,
    }

    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    output = io.BytesIO()

    workbook.save(output)
    output.seek(0)

    filename = (
        "mutasi_asset_export_"
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
# IMPORT ASSET
# ============================================================


@main.route(
    "/assets/<int:asset_id>/movements"
)
@requires_permission("movement", "read")
def asset_movements(asset_id):

    # ========================================================
    # AMBIL ASSET
    # ========================================================

    asset = Asset.query.get_or_404(
        asset_id
    )

    # ========================================================
    # AMBIL SELURUH MOVEMENT ASSET
    #
    # Urutan histori:
    # movement paling lama -> paling baru
    #
    # ID digunakan sebagai secondary ordering apabila
    # terdapat beberapa movement pada tanggal yang sama.
    # ========================================================

    movements = (
        AssetMovement.query
        .filter(
            AssetMovement.asset_id == asset.id
        )
        .order_by(
            AssetMovement.movement_date.asc(),
            AssetMovement.id.asc(),
        )
        .all()
    )

    # ========================================================
    # MOVEMENT TERAKHIR
    #
    # Hanya movement terakhir yang dapat dikoreksi.
    # ========================================================

    last_movement = (
        movements[-1]
        if movements
        else None
    )

    # ========================================================
    # JUMLAH MOVEMENT
    # ========================================================

    movement_count = len(
        movements
    )

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(
        "asset/movements.html",

        asset=asset,

        movements=movements,

        last_movement=last_movement,

        movement_count=movement_count,
    )

# ============================================================
# LAPORAN MUTASI ASSET
# ============================================================


@main.route("/assets/movements/report")
@requires_permission("movement", "read")
def asset_movements_report():

    start_date = parse_date(
        request.args.get("start_date")
    )

    end_date = parse_date(
        request.args.get("end_date")
    )

    query = (
        AssetMovement.query
        .join(
            Asset,
            Asset.id == AssetMovement.asset_id,
        )
    )

    if start_date:

        query = query.filter(
            AssetMovement.movement_date >= start_date
        )

    if end_date:

        query = query.filter(
            AssetMovement.movement_date <= end_date
        )

    movements = (
        query
        .order_by(
            AssetMovement.movement_date.desc(),
            AssetMovement.id.desc(),
        )
        .all()
    )

    total_movements = (
        AssetMovement.query.count()
    )

    filtered_movements = len(movements)

    location_rows = (
        db.session.query(
            AssetMovement.to_location,
            db.func.count(AssetMovement.id),
        )
        .filter(
            AssetMovement.to_location.isnot(None)
        )
        .filter(
            AssetMovement.to_location != ""
        )
        .group_by(
            AssetMovement.to_location
        )
        .order_by(
            db.func.count(
                AssetMovement.id
            ).desc()
        )
        .all()
    )

    top_location = "-"

    if location_rows:
        top_location = location_rows[0][0]

    department_rows = (
        db.session.query(
            AssetMovement.to_department,
            db.func.count(AssetMovement.id),
        )
        .filter(
            AssetMovement.to_department.isnot(None)
        )
        .filter(
            AssetMovement.to_department != ""
        )
        .group_by(
            AssetMovement.to_department
        )
        .order_by(
            db.func.count(
                AssetMovement.id
            ).desc()
        )
        .all()
    )

    top_department = "-"

    if department_rows:
        top_department = department_rows[0][0]

    return render_template(
        "asset/movement_report.html",
        movements=movements,
        start_date=start_date,
        end_date=end_date,
        total_movements=total_movements,
        filtered_movements=filtered_movements,
        top_location=top_location,
        top_department=top_department,
    )

# ============================================================
# GLOBAL ASSET MOVEMENTS
# ============================================================


@main.route("/assets/movements")
@requires_permission("movement", "read")
def global_asset_movements():

    # ========================================================
    # FILTER
    # ========================================================

    search = (
        request.args.get(
            "search",
            ""
        )
        or ""
    ).strip()

    status_filter = (
        request.args.get(
            "status",
            ""
        )
        or ""
    ).strip().upper()

    date_from = (
        request.args.get(
            "date_from",
            ""
        )
        or ""
    ).strip()

    date_to = (
        request.args.get(
            "date_to",
            ""
        )
        or ""
    ).strip()

    location = (
        request.args.get(
            "location",
            ""
        )
        or ""
    ).strip()

    department = (
        request.args.get(
            "department",
            ""
        )
        or ""
    ).strip()

    pic = (
        request.args.get(
            "pic",
            ""
        )
        or ""
    ).strip()

    # ========================================================
    # QUERY DASAR
    # ========================================================

    query = (
        AssetMovement.query
        .join(
            Asset,
            AssetMovement.asset_id
            == Asset.id
        )
    )

    # ========================================================
    # SEARCH
    # ========================================================

    if search:

        search_pattern = (
            f"%{search}%"
        )

        query = query.filter(
            db.or_(

                AssetMovement.movement_no.ilike(
                    search_pattern
                ),

                Asset.asset_tag.ilike(
                    search_pattern
                ),

                Asset.asset_name.ilike(
                    search_pattern
                ),

                AssetMovement.from_location.ilike(
                    search_pattern
                ),

                AssetMovement.to_location.ilike(
                    search_pattern
                ),

                AssetMovement.from_department.ilike(
                    search_pattern
                ),

                AssetMovement.to_department.ilike(
                    search_pattern
                ),

                AssetMovement.from_pic.ilike(
                    search_pattern
                ),

                AssetMovement.to_pic.ilike(
                    search_pattern
                )
            )
        )

    # ========================================================
    # DATE FROM
    # ========================================================

    if date_from:

        parsed_date_from = parse_date(
            date_from
        )

        if parsed_date_from:

            query = query.filter(
                AssetMovement.movement_date
                >= parsed_date_from
            )

    # ========================================================
    # DATE TO
    # ========================================================

    if date_to:

        parsed_date_to = parse_date(
            date_to
        )

        if parsed_date_to:

            query = query.filter(
                AssetMovement.movement_date
                <= parsed_date_to
            )

    # ========================================================
    # LOCATION
    # ========================================================

    if location:

        location_pattern = (
            f"%{location}%"
        )

        query = query.filter(
            db.or_(

                AssetMovement.from_location.ilike(
                    location_pattern
                ),

                AssetMovement.to_location.ilike(
                    location_pattern
                )
            )
        )

    # ========================================================
    # DEPARTMENT
    # ========================================================

    if department:

        department_pattern = (
            f"%{department}%"
        )

        query = query.filter(
            db.or_(

                AssetMovement.from_department.ilike(
                    department_pattern
                ),

                AssetMovement.to_department.ilike(
                    department_pattern
                )
            )
        )

    # ========================================================
    # PIC
    # ========================================================

    if pic:

        pic_pattern = (
            f"%{pic}%"
        )

        query = query.filter(
            db.or_(

                AssetMovement.from_pic.ilike(
                    pic_pattern
                ),

                AssetMovement.to_pic.ilike(
                    pic_pattern
                )
            )
        )

    # ========================================================
    # AMBIL DATA MOVEMENT
    # ========================================================

    movements = (
        query
        .order_by(
            AssetMovement.movement_date.desc(),
            AssetMovement.id.desc()
        )
        .all()
    )

    # ========================================================
    # TENTUKAN MOVEMENT TERAKHIR SETIAP ASSET
    #
    # Dibuat satu kali untuk seluruh asset.
    # Tidak melakukan query berulang di dalam loop.
    # ========================================================

    latest_movement_by_asset = {}

    all_asset_movements = (
        AssetMovement.query
        .order_by(
            AssetMovement.asset_id.asc(),
            AssetMovement.movement_date.desc(),
            AssetMovement.id.desc()
        )
        .all()
    )

    for item in all_asset_movements:

        if item.asset_id not in latest_movement_by_asset:

            latest_movement_by_asset[
                item.asset_id
            ] = item.id

    # ========================================================
    # BENTUK DATA UNTUK TEMPLATE
    # ========================================================

    movement_rows = []

    for movement in movements:

        latest_movement_id = (
            latest_movement_by_asset.get(
                movement.asset_id
            )
        )

        is_current = (
            latest_movement_id is not None
            and
            latest_movement_id
            == movement.id
        )

        movement_status = (
            "CURRENT"
            if is_current
            else "HISTORY"
        )

        # ----------------------------------------------------
        # FILTER STATUS
        # ----------------------------------------------------

        if (
            status_filter
            and
            status_filter
            != movement_status
        ):

            continue

        movement_rows.append({

            "movement": movement,

            "asset": movement.asset,

            "status": movement_status,

        })

    # ========================================================
    # MASTER LOCATION
    # ========================================================

    locations = (
        Location.query
        .order_by(
            Location.name.asc()
        )
        .all()
    )

    # ========================================================
    # MASTER DEPARTMENT
    # ========================================================

    departments = (
        Department.query
        .order_by(
            Department.name.asc()
        )
        .all()
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    total_movements = (
        len(movement_rows)
    )

    current_movements = sum(
        1
        for row in movement_rows
        if row["status"] == "CURRENT"
    )

    history_movements = sum(
        1
        for row in movement_rows
        if row["status"] == "HISTORY"
    )

    # ========================================================
    # PAGINATION (untuk tabel, summary tetap pakai movement_rows)
    # ========================================================

    page = request.args.get(
        "page",
        1,
        type=int,
    )

    pagination = SimplePagination(
        movement_rows,
        page,
        MOVEMENT_LIST_PER_PAGE,
    )

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(
        "asset/movements_global.html",

        movements=movement_rows,

        pagination=pagination,

        search=search,

        status_filter=status_filter,

        date_from=date_from,

        date_to=date_to,

        location=location,

        department=department,

        pic=pic,

        locations=locations,

        departments=departments,

        total_movements=total_movements,

        current_movements=current_movements,

        history_movements=history_movements,

    )


# ============================================================
# EXPORT LAPORAN MUTASI ASSET
# ============================================================

# ============================================================
# EXPORT LAPORAN MUTASI ASSET
# ============================================================


@main.route(
    "/assets/movements/report/export"
)
@requires_permission("movement", "read")
def export_asset_movements_report():

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment

    start_date = parse_date(
        request.args.get("start_date")
    )

    end_date = parse_date(
        request.args.get("end_date")
    )

    query = (
        AssetMovement.query
        .join(
            Asset,
            Asset.id == AssetMovement.asset_id,
        )
    )

    if start_date:

        query = query.filter(
            AssetMovement.movement_date >= start_date
        )

    if end_date:

        query = query.filter(
            AssetMovement.movement_date <= end_date
        )

    movements = (
        query
        .order_by(
            AssetMovement.movement_date.desc(),
            AssetMovement.id.desc(),
        )
        .all()
    )

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "Laporan Mutasi"

    headers = [
        "No",
        "No. Mutasi",
        "Tanggal",
        "Asset Tag",
        "Nama Asset",
        "Category",
        "Dari Lokasi",
        "Ke Lokasi",
        "Dari Department",
        "Ke Department",
        "Dari PIC",
        "Ke PIC",
        "Alasan",
        "Catatan",
        "Penyerah",
        "Jabatan Penyerah",
        "Penerima",
        "Jabatan Penerima",
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

    for number, movement in enumerate(
        movements,
        start=1,
    ):

        asset = movement.asset

        worksheet.append([
            number,
            movement.movement_no or "",
            (
                movement.movement_date.strftime("%d-%m-%Y")
                if movement.movement_date
                else ""
            ),
            asset.asset_tag if asset else "",
            asset.asset_name if asset else "",
            asset.category if asset else "",
            movement.from_location or "",
            movement.to_location or "",
            movement.from_department or "",
            movement.to_department or "",
            movement.from_pic or "",
            movement.to_pic or "",
            movement.reason or "",
            movement.notes or "",
            movement.from_signer_name or "",
            movement.from_signer_position or "",
            movement.to_signer_name or "",
            movement.to_signer_position or "",
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    column_widths = {
        "A": 8,
        "B": 22,
        "C": 15,
        "D": 18,
        "E": 30,
        "F": 20,
        "G": 25,
        "H": 25,
        "I": 25,
        "J": 25,
        "K": 22,
        "L": 22,
        "M": 30,
        "N": 40,
        "O": 25,
        "P": 25,
        "Q": 25,
        "R": 25,
    }

    for column, width in column_widths.items():

        worksheet.column_dimensions[
            column
        ].width = width

    output = io.BytesIO()

    workbook.save(output)
    output.seek(0)

    if start_date and end_date:

        period = (
            f"{start_date.strftime('%Y%m%d')}_"
            f"{end_date.strftime('%Y%m%d')}"
        )

    elif start_date:

        period = (
            f"from_{start_date.strftime('%Y%m%d')}"
        )

    elif end_date:

        period = (
            f"until_{end_date.strftime('%Y%m%d')}"
        )

    else:

        period = "all"

    filename = (
        "laporan_mutasi_"
        + period
        + "_"
        + datetime.now().strftime("%H%M%S")
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
# ASSET MOVEMENT DETAIL / BUKTI MUTASI
# ============================================================


@main.route(
    "/assets/<int:asset_id>/movement/<int:movement_id>"
)
@requires_permission("movement", "read")
def asset_movement_detail(
    asset_id,
    movement_id
):

    # ========================================================
    # AMBIL ASSET
    # ========================================================

    asset = Asset.query.get_or_404(
        asset_id
    )

    # ========================================================
    # AMBIL MOVEMENT
    # ========================================================

    movement = (
        AssetMovement.query
        .filter(
            AssetMovement.id == movement_id,
            AssetMovement.asset_id == asset.id
        )
        .first_or_404()
    )

    # ========================================================
    # DATA PERUSAHAAN
    # ========================================================

    company = (
        Company.query
        .order_by(
            Company.id.asc()
        )
        .first()
    )

    # ========================================================
    # AMBIL RIWAYAT KOREKSI
    #
    # Jangan menggunakan movement.corrections langsung
    # di template karena akan melakukan lazy-load.
    # ========================================================

    corrections = (
        AssetMovementCorrection.query
        .filter(
            AssetMovementCorrection.movement_id
            == movement.id
        )
        .order_by(
            AssetMovementCorrection.corrected_at.desc(),
            AssetMovementCorrection.id.desc()
        )
        .all()
    )

    # ========================================================
    # CEK MOVEMENT TERAKHIR
    # ========================================================

    last_movement = (
        AssetMovement.query
        .filter(
            AssetMovement.asset_id
            == asset.id
        )
        .order_by(
            AssetMovement.movement_date.desc(),
            AssetMovement.id.desc()
        )
        .first()
    )

    is_current_movement = (
        last_movement is not None
        and
        last_movement.id == movement.id
    )

    # ========================================================
    # QR MUTASI
    # ========================================================

    qr_filename = (
        f"movement_{movement.id}.png"
    )

    qr_directory = os.path.join(
        current_app.static_folder,
        "qrcodes"
    )

    qr_path = os.path.join(
        qr_directory,
        qr_filename
    )

    # ========================================================
    # PASTIKAN FOLDER QR ADA
    # ========================================================

    os.makedirs(
        qr_directory,
        exist_ok=True
    )

    # ========================================================
    # GENERATE QR JIKA BELUM ADA
    # ========================================================

    if not os.path.exists(qr_path):

        try:

            generate_asset_movement_qr(
                asset,
                movement
            )

        except Exception as e:

            current_app.logger.error(
                "Movement QR generation error: %s",
                e
            )

    # ========================================================
    # URL VERIFIKASI
    # ========================================================

    verification_url = url_for(
        "main.verify_asset_movement",
        asset_id=asset.id,
        movement_id=movement.id,
        _external=True
    )

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(
        "asset/movement_detail.html",

        asset=asset,

        movement=movement,

        company=company,

        corrections=corrections,

        last_movement=last_movement,

        is_current_movement=is_current_movement,

        qr_filename=qr_filename,

        verification_url=verification_url
    )

# ============================================================
# ASSET MOVEMENT CORRECTION HISTORY
# ============================================================


@main.route(
    "/assets/<int:asset_id>/movement/<int:movement_id>/corrections"
)
@requires_permission("movement", "read")
def asset_movement_corrections(
    asset_id,
    movement_id
):

    # ========================================================
    # AMBIL ASSET
    # ========================================================

    asset = Asset.query.get_or_404(
        asset_id
    )

    # ========================================================
    # AMBIL MOVEMENT
    # ========================================================

    movement = (
        AssetMovement.query
        .filter(
            AssetMovement.id == movement_id,
            AssetMovement.asset_id == asset_id
        )
        .first_or_404()
    )

    # ========================================================
    # AMBIL RIWAYAT KOREKSI
    # ========================================================

    corrections = (
        AssetMovementCorrection.query
        .filter(
            AssetMovementCorrection.movement_id
            == movement.id
        )
        .order_by(
            AssetMovementCorrection.corrected_at.desc(),
            AssetMovementCorrection.id.desc()
        )
        .all()
    )

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(
        "asset/movement_corrections.html",

        asset=asset,

        movement=movement,

        corrections=corrections,
    )

# ============================================================
# ASSET MOVEMENT QR
# ============================================================


@main.route(
    "/assets/<int:asset_id>/movement/<int:movement_id>/qr"
)
@requires_permission("movement", "read")
def asset_movement_qr(asset_id, movement_id):

    asset = Asset.query.get_or_404(
        asset_id
    )

    movement = (
        AssetMovement.query
        .filter_by(
            id=movement_id,
            asset_id=asset.id
        )
        .first_or_404()
    )

    # ========================================================
    # GENERATE QR
    # ========================================================

    qr_filename = generate_asset_movement_qr(
        asset,
        movement
    )

    # ========================================================
    # URL VERIFIKASI
    # ========================================================

    verification_url = url_for(
        "main.verify_asset_movement",
        asset_id=asset.id,
        movement_id=movement.id,
        _external=True
    )

    # ========================================================
    # RENDER
    # ========================================================

    return render_template(
        "asset/movement_qr.html",
        asset=asset,
        movement=movement,
        qr_filename=qr_filename,
        verification_url=verification_url
    )

# ============================================================
# ASSET MOVEMENT QR IMAGE
# ============================================================


@main.route(
    "/assets/<int:asset_id>/movement/<int:movement_id>/qr/image"
)
@requires_permission("movement", "read")
def asset_movement_qr_image(asset_id, movement_id):

    asset = Asset.query.get_or_404(
        asset_id
    )

    movement = (
        AssetMovement.query
        .filter_by(
            id=movement_id,
            asset_id=asset.id
        )
        .first_or_404()
    )

    qr_folder = os.path.join(
        current_app.static_folder,
        "qrcodes"
    )

    os.makedirs(
        qr_folder,
        exist_ok=True
    )

    qr_filename = (
        f"movement_{movement.id}.png"
    )

    qr_path = os.path.join(
        qr_folder,
        qr_filename
    )

    if not os.path.exists(qr_path):

        generate_asset_movement_qr(
            asset,
            movement
        )

    if not os.path.exists(qr_path):

        return (
            "QR Code mutasi tidak berhasil dibuat.",
            500
        )

    return send_file(
        qr_path,
        mimetype="image/png"
    )

# ============================================================
# VERIFIKASI MUTASI ASSET
# ============================================================


@main.route(
    "/verify/movement/<int:asset_id>/<int:movement_id>"
)
def verify_asset_movement(asset_id, movement_id):

    asset = Asset.query.get_or_404(
        asset_id
    )

    movement = (
        AssetMovement.query
        .filter_by(
            id=movement_id,
            asset_id=asset.id
        )
        .first_or_404()
    )

    return render_template(
        "asset/movement_verify.html",
        asset=asset,
        movement=movement
    )

# ============================================================
# DASHBOARD ANALYTICS
# ============================================================


@main.route(
    "/assets/<int:asset_id>/movement/add",
    methods=["GET", "POST"],
)
@requires_permission("movement", "create")
def add_asset_movement(asset_id):

    # ========================================================
    # AMBIL ASSET
    # ========================================================

    asset = Asset.query.get_or_404(
        asset_id
    )

    # ========================================================
    # MASTER DATA
    # ========================================================

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

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return render_template(
            "asset/movement_add.html",
            asset=asset,
            locations=locations,
            departments=departments,
        )

    # ========================================================
    # TANGGAL MOVEMENT
    # ========================================================

    movement_date = parse_date(
        request.form.get(
            "movement_date"
        )
    )

    if not movement_date:

        flash(
            _("Movement date is required."),
            "danger",
        )

        return render_template(
            "asset/movement_add.html",
            asset=asset,
            locations=locations,
            departments=departments,
        )

    # ========================================================
    # FROM
    #
    # FROM SELALU MENGAMBIL KONDISI ASSET TERKINI
    # DARI DATABASE.
    #
    # USER TIDAK BOLEH MENENTUKAN FROM MELALUI FORM.
    # ========================================================

    from_location = (
        asset.location
        or ""
    ).strip()

    from_department = (
        asset.department
        or ""
    ).strip()

    from_pic = (
        asset.pic
        or ""
    ).strip()

    # ========================================================
    # TO
    #
    # TO DIISI OLEH USER.
    # ========================================================

    to_location = (
        request.form.get(
            "to_location"
        )
        or ""
    ).strip()

    to_department = (
        request.form.get(
            "to_department"
        )
        or ""
    ).strip()

    to_pic = (
        request.form.get(
            "to_pic"
        )
        or ""
    ).strip()

    # ========================================================
    # DATA TAMBAHAN
    # ========================================================

    reason = (
        request.form.get(
            "reason"
        )
        or ""
    ).strip()

    notes = (
        request.form.get(
            "notes"
        )
        or ""
    ).strip()

    # ========================================================
    # SIGNER FROM
    # ========================================================

    from_signer_name = (
        request.form.get(
            "from_signer_name"
        )
        or ""
    ).strip()

    from_signer_position = (
        request.form.get(
            "from_signer_position"
        )
        or ""
    ).strip()

    # ========================================================
    # SIGNER TO
    # ========================================================

    to_signer_name = (
        request.form.get(
            "to_signer_name"
        )
        or ""
    ).strip()

    to_signer_position = (
        request.form.get(
            "to_signer_position"
        )
        or ""
    ).strip()

    # ========================================================
    # SIGNATURE FROM
    # ========================================================

    from_signature = (
        request.form.get(
            "from_signature"
        )
        or ""
    ).strip()

    # ========================================================
    # SIGNATURE TO
    # ========================================================

    to_signature = (
        request.form.get(
            "to_signature"
        )
        or ""
    ).strip()

    # ========================================================
    # VALIDASI FROM
    #
    # Jika asset belum mempunyai data lokasi / department /
    # PIC, movement tetap dapat diproses selama TO lengkap.
    # ========================================================

    # ========================================================
    # VALIDASI TO LOCATION
    # ========================================================

    if not to_location:

        flash(
            _("Destination location is required."),
            "danger",
        )

        return render_template(
            "asset/movement_add.html",
            asset=asset,
            locations=locations,
            departments=departments,
        )

    # ========================================================
    # VALIDASI TO DEPARTMENT
    # ========================================================

    if not to_department:

        flash(
            _("Destination department is required."),
            "danger",
        )

        return render_template(
            "asset/movement_add.html",
            asset=asset,
            locations=locations,
            departments=departments,
        )

    # ========================================================
    # VALIDASI TO PIC
    # ========================================================

    if not to_pic:

        flash(
            _("Destination PIC is required."),
            "danger",
        )

        return render_template(
            "asset/movement_add.html",
            asset=asset,
            locations=locations,
            departments=departments,
        )

    # ========================================================
    # CEK APAKAH ADA PERUBAHAN
    # ========================================================

    if (
        from_location == to_location
        and
        from_department == to_department
        and
        from_pic == to_pic
    ):

        flash(
            _("Movement has no change in asset position."),
            "warning",
        )

        return render_template(
            "asset/movement_add.html",
            asset=asset,
            locations=locations,
            departments=departments,
        )

    # ========================================================
    # CEK MOVEMENT TERAKHIR
    #
    # Kondisi asset harus sama dengan TO movement terakhir.
    #
    # Ini memastikan database asset dan histori movement
    # tidak berjalan pada posisi yang berbeda.
    # ========================================================

    latest_movement = (
        AssetMovement.query
        .filter_by(
            asset_id=asset.id
        )
        .order_by(
            AssetMovement.id.desc()
        )
        .first()
    )

    if latest_movement:

        latest_to_location = (
            latest_movement.to_location
            or ""
        ).strip()

        latest_to_department = (
            latest_movement.to_department
            or ""
        ).strip()

        latest_to_pic = (
            latest_movement.to_pic
            or ""
        ).strip()

        asset_location = (
            asset.location
            or ""
        ).strip()

        asset_department = (
            asset.department
            or ""
        ).strip()

        asset_pic = (
            asset.pic
            or ""
        ).strip()

        if (
            asset_location != latest_to_location
            or
            asset_department != latest_to_department
            or
            asset_pic != latest_to_pic
        ):

            flash(
                _(
                    "Asset data is not in sync with the latest movement. "
                    "Please check and correct the asset data before "
                    "creating a new movement."
                ),
                "danger",
            )

            return render_template(
                "asset/movement_add.html",
                asset=asset,
                locations=locations,
                departments=departments,
            )

    # ========================================================
    # GENERATE NOMOR MOVEMENT
    # ========================================================

    last_movement = (
        AssetMovement.query
        .order_by(
            AssetMovement.id.desc()
        )
        .first()
    )

    next_number = (
        last_movement.id + 1
        if last_movement
        else 1
    )

    movement_no = (
        f"MT-{movement_date.strftime('%Y%m%d')}-"
        f"{next_number:04d}"
    )

    # ========================================================
    # BUAT OBJECT MOVEMENT
    # ========================================================

    movement = AssetMovement(

        movement_no=movement_no,

        asset_id=asset.id,

        movement_date=movement_date,

        # ----------------------------------------------------
        # FROM
        # ----------------------------------------------------

        from_location=from_location,

        from_department=from_department,

        from_pic=from_pic,

        # ----------------------------------------------------
        # TO
        # ----------------------------------------------------

        to_location=to_location,

        to_department=to_department,

        to_pic=to_pic,

        # ----------------------------------------------------
        # SIGNER FROM
        # ----------------------------------------------------

        from_signer_name=from_signer_name,

        from_signer_position=from_signer_position,

        # ----------------------------------------------------
        # SIGNER TO
        # ----------------------------------------------------

        to_signer_name=to_signer_name,

        to_signer_position=to_signer_position,

        # ----------------------------------------------------
        # SIGNATURE FROM
        # ----------------------------------------------------

        from_signature=from_signature,

        # ----------------------------------------------------
        # SIGNATURE TO
        # ----------------------------------------------------

        to_signature=to_signature,

        # ----------------------------------------------------
        # KETERANGAN
        # ----------------------------------------------------

        reason=reason,

        notes=notes,

        # ----------------------------------------------------
        # CREATED
        # ----------------------------------------------------

        created_at=datetime.utcnow(),
    )

    # ========================================================
    # UPDATE ASSET
    #
    # Setelah movement berhasil dibuat, kondisi asset harus
    # sama persis dengan TO movement.
    # ========================================================

    asset.location = (
        to_location
    )

    asset.department = (
        to_department
    )

    asset.pic = (
        to_pic
    )

    # ========================================================
    # SIMPAN DATABASE
    # ========================================================

    try:

        db.session.add(
            movement
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(
            "Gagal menyimpan asset movement."
        )

        flash(
            _("Failed to save the movement. Detail: %(error)s")
            % {"error": str(e)},
            "danger",
        )

        return render_template(
            "asset/movement_add.html",
            asset=asset,
            locations=locations,
            departments=departments,
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    flash(
        _("Asset movement saved successfully. Movement number: %(number)s")
        % {"number": movement_no},
        "success",
    )

    # ========================================================
    # REDIRECT DETAIL MOVEMENT
    # ========================================================

    return redirect(
        url_for(
            "main.asset_movement_detail",
            asset_id=asset.id,
            movement_id=movement.id,
        )
    )

# ============================================================
# KOREKSI ASSET MOVEMENT
# ============================================================


@main.route(
    "/assets/<int:asset_id>/movement/<int:movement_id>/correct",
    methods=["GET", "POST"],
)
@requires_permission("movement", "edit")
def correct_asset_movement(
    asset_id,
    movement_id
):

    # ========================================================
    # AMBIL ASSET
    # ========================================================

    asset = Asset.query.get_or_404(
        asset_id
    )

    # ========================================================
    # AMBIL MOVEMENT
    # ========================================================

    movement = (
        AssetMovement.query
        .filter_by(
            id=movement_id,
            asset_id=asset.id
        )
        .first_or_404()
    )

    # ========================================================
    # CEK MOVEMENT TERAKHIR
    #
    # HANYA MOVEMENT TERAKHIR YANG BOLEH DIKOREKSI.
    #
    # Hal ini menjaga histori movement tetap konsisten.
    # ========================================================

    latest_movement = (
        AssetMovement.query
        .filter_by(
            asset_id=asset.id
        )
        .order_by(
            AssetMovement.id.desc()
        )
        .first()
    )

    if not latest_movement:

        flash(
            _("Movement not found."),
            "danger"
        )

        return redirect(
            url_for(
                "main.asset_detail",
                asset_id=asset.id
            )
        )

    if latest_movement.id != movement.id:

        flash(
            _(
                "This movement is not the latest movement for this "
                "asset. Only the latest movement can be corrected."
            ),
            "warning"
        )

        return redirect(
            url_for(
                "main.asset_movement_detail",
                asset_id=asset.id,
                movement_id=movement.id
            )
        )

    # ========================================================
    # CARI MOVEMENT SEBELUMNYA
    #
    # FROM movement saat ini harus sama dengan TO
    # movement sebelumnya.
    #
    # Ini adalah bagian penting untuk menjaga histori.
    # ========================================================

    previous_movement = (
        AssetMovement.query
        .filter(
            AssetMovement.asset_id == asset.id,
            AssetMovement.id < movement.id,
        )
        .order_by(
            AssetMovement.id.desc()
        )
        .first()
    )

    # ========================================================
    # TENTUKAN FROM YANG BENAR
    #
    # Jika ada movement sebelumnya:
    #
    # FROM LOCATION    = TO LOCATION sebelumnya
    # FROM DEPARTMENT  = TO DEPARTMENT sebelumnya
    # FROM PIC         = TO PIC sebelumnya
    #
    # Jika ini movement pertama:
    # FROM dipertahankan dari data movement saat ini.
    # ========================================================

    if previous_movement:

        correct_from_location = (
            previous_movement.to_location
            or ""
        ).strip()

        correct_from_department = (
            previous_movement.to_department
            or ""
        ).strip()

        correct_from_pic = (
            previous_movement.to_pic
            or ""
        ).strip()

    else:

        correct_from_location = (
            movement.from_location
            or ""
        ).strip()

        correct_from_department = (
            movement.from_department
            or ""
        ).strip()

        correct_from_pic = (
            movement.from_pic
            or ""
        ).strip()

    # ========================================================
    # MASTER DATA
    # ========================================================

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

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # POST
    # ========================================================

    movement_date = parse_date(
        request.form.get(
            "movement_date"
        )
    )

    # ========================================================
    # VALIDASI TANGGAL
    # ========================================================

    if not movement_date:

        flash(
            _("Movement date is required."),
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # VALIDASI URUTAN TANGGAL
    #
    # Movement terakhir tidak boleh memiliki tanggal
    # sebelum movement sebelumnya.
    # ========================================================

    if (
        previous_movement
        and previous_movement.movement_date
        and movement_date < previous_movement.movement_date
    ):

        flash(
            _(
                "Movement date cannot be earlier than the previous "
                "movement."
            ),
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # TO DIAMBIL DARI FORM
    #
    # FROM SENGAJA TIDAK DIAMBIL DARI FORM.
    #
    # FROM ditentukan berdasarkan histori database.
    # ========================================================

    to_location = (
        request.form.get(
            "to_location"
        )
        or ""
    ).strip()

    to_department = (
        request.form.get(
            "to_department"
        )
        or ""
    ).strip()

    to_pic = (
        request.form.get(
            "to_pic"
        )
        or ""
    ).strip()

    # ========================================================
    # DATA TAMBAHAN
    # ========================================================

    reason = (
        request.form.get(
            "reason"
        )
        or ""
    ).strip()

    notes = (
        request.form.get(
            "notes"
        )
        or ""
    ).strip()

    from_signer_name = (
        request.form.get(
            "from_signer_name"
        )
        or ""
    ).strip()

    from_signer_position = (
        request.form.get(
            "from_signer_position"
        )
        or ""
    ).strip()

    to_signer_name = (
        request.form.get(
            "to_signer_name"
        )
        or ""
    ).strip()

    to_signer_position = (
        request.form.get(
            "to_signer_position"
        )
        or ""
    ).strip()

    from_signature = (
        request.form.get(
            "from_signature"
        )
        or ""
    ).strip()

    to_signature = (
        request.form.get(
            "to_signature"
        )
        or ""
    ).strip()

    # ========================================================
    # VALIDASI FROM
    #
    # Validasi dilakukan terhadap hasil database,
    # bukan terhadap input user.
    # ========================================================

    if not correct_from_location:

        flash(
            _(
                "The movement's origin location could not be "
                "determined from the asset history."
            ),
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    if not correct_from_department:

        flash(
            _(
                "The movement's origin department could not be "
                "determined from the asset history."
            ),
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # VALIDASI TO LOCATION
    # ========================================================

    if not to_location:

        flash(
            _("Destination location is required."),
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # VALIDASI TO DEPARTMENT
    # ========================================================

    if not to_department:

        flash(
            _("Destination department is required."),
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # VALIDASI TO PIC
    # ========================================================

    if not to_pic:

        flash(
            _("Destination PIC is required."),
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # CEK APAKAH ADA PERUBAHAN
    # ========================================================

    if (
        correct_from_location == to_location
        and
        correct_from_department == to_department
        and
        correct_from_pic == to_pic
    ):

        flash(
            _("Movement has no change in asset position."),
            "warning"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

    # ========================================================
    # UPDATE MOVEMENT
    # ========================================================

    movement.movement_date = movement_date

    # --------------------------------------------------------
    # FROM
    #
    # SELALU BERASAL DARI HISTORI DATABASE.
    # --------------------------------------------------------

    movement.from_location = (
        correct_from_location
    )

    movement.from_department = (
        correct_from_department
    )

    movement.from_pic = (
        correct_from_pic
    )

    # --------------------------------------------------------
    # TO
    # --------------------------------------------------------

    movement.to_location = (
        to_location
    )

    movement.to_department = (
        to_department
    )

    movement.to_pic = (
        to_pic
    )

    # --------------------------------------------------------
    # SIGNER
    # --------------------------------------------------------

    movement.from_signer_name = (
        from_signer_name
    )

    movement.from_signer_position = (
        from_signer_position
    )

    movement.to_signer_name = (
        to_signer_name
    )

    movement.to_signer_position = (
        to_signer_position
    )

    # --------------------------------------------------------
    # SIGNATURE
    # --------------------------------------------------------

    movement.from_signature = (
        from_signature
    )

    movement.to_signature = (
        to_signature
    )

    # --------------------------------------------------------
    # KETERANGAN
    # --------------------------------------------------------

    movement.reason = (
        reason
    )

    movement.notes = (
        notes
    )

    # ========================================================
    # UPDATE ASSET
    #
    # Karena movement yang dikoreksi adalah movement terakhir,
    # kondisi asset harus mengikuti nilai TO terbaru.
    # ========================================================

    asset.location = (
        to_location
    )

    asset.department = (
        to_department
    )

    asset.pic = (
        to_pic
    )

    # ========================================================
    # SIMPAN DATABASE
    # ========================================================

    try:

        db.session.commit()

        # ====================================================
        # HAPUS QR LAMA
        #
        # QR akan dibuat ulang ketika detail movement dibuka.
        # ====================================================

        qr_filename = (
            f"movement_{movement.id}.png"
        )

        qr_path = os.path.join(
            current_app.static_folder,
            "qrcodes",
            qr_filename
        )

        if os.path.exists(
            qr_path
        ):

            try:

                os.remove(
                    qr_path
                )

            except OSError:

                pass

        # ====================================================
        # SUCCESS
        # ====================================================

        flash(
            _("Movement %(number)s corrected successfully.")
            % {"number": movement.movement_no or "-"},
            "success"
        )

        return redirect(
            url_for(
                "main.asset_movement_detail",
                asset_id=asset.id,
                movement_id=movement.id
            )
        )

    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(
            "ERROR KOREKSI MOVEMENT"
        )

        flash(
            _("An error occurred while saving the movement correction. "
              "Detail: %(error)s")
            % {"error": str(e)},
            "danger"
        )

        return render_template(
            "asset/movement_correct.html",
            asset=asset,
            movement=movement,
            locations=locations,
            departments=departments,
            correct_from_location=correct_from_location,
            correct_from_department=correct_from_department,
            correct_from_pic=correct_from_pic,
        )

# ============================================================
# CATEGORY
# ============================================================


