"""
Master data: kategori, lokasi, departemen, vendor.
"""

from flask import render_template, request, redirect, url_for, flash
from flask_babel import gettext as _

from .. import db
from ..models import Category, Location, Department, Vendor
from ..auth import requires_permission

from . import main
from .helpers import log_action

@main.route("/categories")
@requires_permission("category", "read")
def categories():

    items = (
        Category.query
        .order_by(Category.name.asc())
        .all()
    )

    return render_template(
        "master/category/list.html",
        categories=items,
    )

# ============================================================
# ADD CATEGORY
# ============================================================


@main.route(
    "/categories/add",
    methods=["GET", "POST"],
)
@requires_permission("category", "create")
def add_category():

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        ).strip()

        if not name:

            flash(
                _("Category name is required."),
                "danger",
            )

            return render_template(
                "master/category/add.html"
            )

        existing = Category.query.filter_by(
            name=name
        ).first()

        if existing:

            flash(
                _("Category already exists."),
                "danger",
            )

            return render_template(
                "master/category/add.html"
            )

        category = Category(
            name=name,
            description=description,
        )

        db.session.add(category)
        db.session.commit()

        log_action("create", "Category", entity_label=category.name)

        flash(
            _("Category added successfully."),
            "success",
        )

        return redirect(
            url_for("main.categories")
        )

    return render_template(
        "master/category/add.html"
    )

# ============================================================
# EDIT CATEGORY
# ============================================================


@main.route(
    "/categories/<int:category_id>/edit",
    methods=["GET", "POST"],
)
@requires_permission("category", "edit")
def edit_category(category_id):

    category = Category.query.get_or_404(
        category_id
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        ).strip()

        if not name:

            flash(
                _("Category name is required."),
                "danger",
            )

            return render_template(
                "master/category/edit.html",
                category=category,
            )

        existing = Category.query.filter(
            Category.name == name,
            Category.id != category.id,
        ).first()

        if existing:

            flash(
                _("Category already exists."),
                "danger",
            )

            return render_template(
                "master/category/edit.html",
                category=category,
            )

        category.name = name
        category.description = description

        db.session.commit()

        log_action("update", "Category", entity_label=category.name)

        flash(
            _("Category updated successfully."),
            "success",
        )

        return redirect(
            url_for("main.categories")
        )

    return render_template(
        "master/category/edit.html",
        category=category,
    )

# ============================================================
# DELETE CATEGORY
# ============================================================


@main.route(
    "/categories/<int:category_id>/delete",
    methods=["POST"],
)
@requires_permission("category", "delete")
def delete_category(category_id):

    category = Category.query.get_or_404(
        category_id
    )

    deleted_name = category.name

    db.session.delete(category)
    db.session.commit()

    log_action("delete", "Category", entity_label=deleted_name)

    flash(
        _("Category deleted successfully."),
        "success",
    )

    return redirect(
        url_for("main.categories")
    )

# ============================================================
# LOCATION
# ============================================================


@main.route("/locations")
@requires_permission("location", "read")
def locations():

    items = (
        Location.query
        .order_by(Location.name.asc())
        .all()
    )

    return render_template(
        "master/location/list.html",
        locations=items,
    )

# ============================================================
# ADD LOCATION
# ============================================================


@main.route(
    "/locations/add",
    methods=["GET", "POST"],
)
@requires_permission("location", "create")
def add_location():

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        )

        if not name:

            flash(
                _("Location name is required."),
                "danger",
            )

            return render_template(
                "master/location/add.html"
            )

        existing = Location.query.filter_by(
            name=name
        ).first()

        if existing:

            flash(
                _("Location already exists."),
                "danger",
            )

            return render_template(
                "master/location/add.html"
            )

        location = Location(
            name=name,
            description=description,
        )

        db.session.add(location)
        db.session.commit()

        log_action("create", "Location", entity_label=location.name)

        flash(
            _("Location added successfully."),
            "success",
        )

        return redirect(
            url_for("main.locations")
        )

    return render_template(
        "master/location/add.html"
    )

# ============================================================
# EDIT LOCATION
# ============================================================


@main.route(
    "/locations/<int:location_id>/edit",
    methods=["GET", "POST"],
)
@requires_permission("location", "edit")
def edit_location(location_id):

    location = Location.query.get_or_404(
        location_id
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        )

        if not name:

            flash(
                _("Location name is required."),
                "danger",
            )

            return render_template(
                "master/location/edit.html",
                location=location,
            )

        duplicate = Location.query.filter(
            Location.name == name,
            Location.id != location.id,
        ).first()

        if duplicate:

            flash(
                _("Location already exists."),
                "danger",
            )

            return render_template(
                "master/location/edit.html",
                location=location,
            )

        location.name = name
        location.description = description

        db.session.commit()

        log_action("update", "Location", entity_label=location.name)

        flash(
            _("Location updated successfully."),
            "success",
        )

        return redirect(
            url_for("main.locations")
        )

    return render_template(
        "master/location/edit.html",
        location=location,
    )

# ============================================================
# DELETE LOCATION
# ============================================================


@main.route(
    "/locations/<int:location_id>/delete",
    methods=["POST"],
)
@requires_permission("location", "delete")
def delete_location(location_id):

    location = Location.query.get_or_404(
        location_id
    )

    deleted_name = location.name

    db.session.delete(location)
    db.session.commit()

    log_action("delete", "Location", entity_label=deleted_name)

    flash(
        _("Location deleted successfully."),
        "success",
    )

    return redirect(
        url_for("main.locations")
    )

# ============================================================
# DEPARTMENT
# ============================================================


@main.route("/departments")
@requires_permission("department", "read")
def departments():

    items = (
        Department.query
        .order_by(Department.name.asc())
        .all()
    )

    return render_template(
        "master/department/list.html",
        departments=items,
    )

# ============================================================
# ADD DEPARTMENT
# ============================================================


@main.route(
    "/departments/add",
    methods=["GET", "POST"],
)
@requires_permission("department", "create")
def add_department():

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        )

        if not name:

            flash(
                _("Department name is required."),
                "danger",
            )

            return render_template(
                "master/department/add.html"
            )

        existing = Department.query.filter_by(
            name=name
        ).first()

        if existing:

            flash(
                _("Department already exists."),
                "danger",
            )

            return render_template(
                "master/department/add.html"
            )

        department = Department(
            name=name,
            description=description,
        )

        db.session.add(department)
        db.session.commit()

        log_action("create", "Department", entity_label=department.name)

        flash(
            _("Department added successfully."),
            "success",
        )

        return redirect(
            url_for("main.departments")
        )

    return render_template(
        "master/department/add.html"
    )

# ============================================================
# EDIT DEPARTMENT
# ============================================================


@main.route(
    "/departments/<int:department_id>/edit",
    methods=["GET", "POST"],
)
@requires_permission("department", "edit")
def edit_department(department_id):

    department = Department.query.get_or_404(
        department_id
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        )

        if not name:

            flash(
                _("Department name is required."),
                "danger",
            )

            return render_template(
                "master/department/edit.html",
                department=department,
            )

        duplicate = Department.query.filter(
            Department.name == name,
            Department.id != department.id,
        ).first()

        if duplicate:

            flash(
                _("Department already exists."),
                "danger",
            )

            return render_template(
                "master/department/edit.html",
                department=department,
            )

        department.name = name
        department.description = description

        db.session.commit()

        log_action("update", "Department", entity_label=department.name)

        flash(
            _("Department updated successfully."),
            "success",
        )

        return redirect(
            url_for("main.departments")
        )

    return render_template(
        "master/department/edit.html",
        department=department,
    )

# ============================================================
# DELETE DEPARTMENT
# ============================================================


@main.route(
    "/departments/<int:department_id>/delete",
    methods=["POST"],
)
@requires_permission("department", "delete")
def delete_department(department_id):

    department = Department.query.get_or_404(
        department_id
    )

    deleted_name = department.name

    db.session.delete(department)
    db.session.commit()

    log_action("delete", "Department", entity_label=deleted_name)

    flash(
        _("Department deleted successfully."),
        "success",
    )

    return redirect(
        url_for("main.departments")
    )

# ============================================================
# VENDOR
# ============================================================


@main.route("/vendors")
@requires_permission("vendor", "read")
def vendors():

    items = (
        Vendor.query
        .order_by(Vendor.name.asc())
        .all()
    )

    return render_template(
        "master/vendor/list.html",
        vendors=items,
    )

# ============================================================
# ADD VENDOR
# ============================================================


@main.route(
    "/vendors/add",
    methods=["GET", "POST"],
)
@requires_permission("vendor", "create")
def add_vendor():

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        if not name:

            flash(
                _("Vendor name is required."),
                "danger",
            )

            return render_template(
                "master/vendor/add.html"
            )

        existing = Vendor.query.filter_by(
            name=name
        ).first()

        if existing:

            flash(
                _("Vendor already exists."),
                "danger",
            )

            return render_template(
                "master/vendor/add.html"
            )

        vendor = Vendor(
            name=name,
            contact_person=request.form.get(
                "contact_person"
            ),
            phone=request.form.get(
                "phone"
            ),
            email=request.form.get(
                "email"
            ),
            address=request.form.get(
                "address"
            ),
            description=request.form.get(
                "description"
            ),
        )

        db.session.add(vendor)
        db.session.commit()

        log_action("create", "Vendor", entity_label=vendor.name)

        flash(
            _("Vendor added successfully."),
            "success",
        )

        return redirect(
            url_for("main.vendors")
        )

    return render_template(
        "master/vendor/add.html"
    )

# ============================================================
# EDIT VENDOR
# ============================================================


@main.route(
    "/vendors/<int:vendor_id>/edit",
    methods=["GET", "POST"],
)
@requires_permission("vendor", "edit")
def edit_vendor(vendor_id):

    vendor = Vendor.query.get_or_404(
        vendor_id
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        if not name:

            flash(
                _("Vendor name is required."),
                "danger",
            )

            return render_template(
                "master/vendor/edit.html",
                vendor=vendor,
            )

        duplicate = Vendor.query.filter(
            Vendor.name == name,
            Vendor.id != vendor.id,
        ).first()

        if duplicate:

            flash(
                _("Vendor already exists."),
                "danger",
            )

            return render_template(
                "master/vendor/edit.html",
                vendor=vendor,
            )

        vendor.name = name

        vendor.contact_person = request.form.get(
            "contact_person"
        )

        vendor.phone = request.form.get(
            "phone"
        )

        vendor.email = request.form.get(
            "email"
        )

        vendor.address = request.form.get(
            "address"
        )

        vendor.description = request.form.get(
            "description"
        )

        db.session.commit()

        log_action("update", "Vendor", entity_label=vendor.name)

        flash(
            _("Vendor updated successfully."),
            "success",
        )

        return redirect(
            url_for("main.vendors")
        )

    return render_template(
        "master/vendor/edit.html",
        vendor=vendor,
    )

# ============================================================
# DELETE VENDOR
# ============================================================


@main.route(
    "/vendors/<int:vendor_id>/delete",
    methods=["POST"],
)
@requires_permission("vendor", "delete")
def delete_vendor(vendor_id):

    vendor = Vendor.query.get_or_404(
        vendor_id
    )

    deleted_name = vendor.name

    db.session.delete(vendor)
    db.session.commit()

    log_action("delete", "Vendor", entity_label=deleted_name)

    flash(
        _("Vendor deleted successfully."),
        "success",
    )

    return redirect(
        url_for("main.vendors")
    )

# ============================================================
# COMPANY
# ============================================================


