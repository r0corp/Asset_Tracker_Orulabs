from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


# ============================================================
# USER (LOGIN & HAK AKSES)
# ============================================================

ROLE_ADMINISTRATOR = "administrator"
ROLE_ADMIN = "admin"
ROLE_USER = "user"

ROLE_CHOICES = [
    ROLE_ADMINISTRATOR,
    ROLE_ADMIN,
    ROLE_USER,
]


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    full_name = db.Column(
        db.String(100),
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default=ROLE_USER,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
    )

    last_seen = db.Column(
        db.DateTime,
        nullable=True,
    )

    ONLINE_THRESHOLD_SECONDS = 120

    @property
    def is_online(self):

        if not self.last_seen:
            return False

        return (
            datetime.utcnow() - self.last_seen
        ).total_seconds() < self.ONLINE_THRESHOLD_SECONDS

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password,
        )

    def __repr__(self):

        return f"<User {self.username} ({self.role})>"

# ============================================================
# MENU (NAVIGASI DINAMIS)
# ============================================================


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    label = db.Column(
        db.String(100),
        nullable=False,
    )

    icon = db.Column(
        db.String(50),
        nullable=True,
    )

    url = db.Column(
        db.String(255),
        nullable=True,
    )

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("menu_items.id"),
        nullable=True,
    )

    order = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    # Comma-separated role list (administrator,admin,user).
    # Kosong/None berarti terlihat oleh semua role.
    roles = db.Column(
        db.String(100),
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    # Kalau True, item ini dirender sebagai garis pemisah di sidebar
    # (label/url/icon diabaikan) - bukan link yang bisa diklik.
    is_divider = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
    )

    children = db.relationship(
        "MenuItem",
        backref=db.backref(
            "parent",
            remote_side=[id],
        ),
        order_by="MenuItem.order, MenuItem.id",
        cascade="all, delete-orphan",
    )

    def allowed_roles(self):

        if not self.roles:
            return []

        return [
            r.strip()
            for r in self.roles.split(",")
            if r.strip()
        ]

    def is_visible_to(self, role):

        allowed = self.allowed_roles()

        return (
            not allowed
            or role in allowed
        )

    def __repr__(self):

        return f"<MenuItem {self.label}>"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


class Vendor(db.Model):
    __tablename__ = "vendors"

    id = db.Column(db.Integer, primary_key=True, nullable=True)
    name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    address = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )

    asset_tag = db.Column(
        db.String(30),
        nullable=False
    )

    asset_name = db.Column(
        db.String(100),
        nullable=False
    )

    photo = db.Column(
        db.String(255),
        nullable=True,
    )

    category = db.Column(
        db.String(50)
    )

    brand = db.Column(
        db.String(50)
    )

    model = db.Column(
        db.String(100)
    )

    serial_number = db.Column(
        db.String(100)
    )

    location = db.Column(
        db.String(100)
    )

    department = db.Column(
        db.String(100)
    )

    pic = db.Column(
        db.String(100)
    )

    purchase_date = db.Column(
        db.Date
    )

    purchase_price = db.Column(
        db.Float
    )

    status = db.Column(
        db.String(30)
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    vendor = db.Column(
        db.String(100)
    )

    warranty = db.Column(
        db.String(100)
    )

    movements = db.relationship(
        "AssetMovement",
        back_populates="asset",
        cascade="all, delete-orphan"
    )

# ============================================================
# WARRANTY HISTORY
# ============================================================


class WarrantyHistory(db.Model):

    __tablename__ = "warranty_histories"

    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False
    )

    # Warranty sebelum perubahan
    old_warranty = db.Column(
        db.String(100),
        nullable=True
    )

    old_end_date = db.Column(
        db.Date,
        nullable=True
    )

    # Warranty setelah perubahan
    new_warranty = db.Column(
        db.String(100),
        nullable=True
    )

    new_end_date = db.Column(
        db.Date,
        nullable=True
    )

    # Tanggal perubahan
    changed_date = db.Column(
        db.Date,
        nullable=False
    )

    # Keterangan
    reason = db.Column(
        db.String(255),
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # Relasi ke Asset
    asset = db.relationship(
        "Asset",
        backref=db.backref(
            "warranty_histories",
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):

        return (
            f"<WarrantyHistory "
            f"{self.asset_id} "
            f"{self.old_warranty} "
            f"-> "
            f"{self.new_warranty}>"
        )


class AssetMovement(db.Model):
    __tablename__ = "asset_movements"

    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )

    movement_no = db.Column(
        db.String(30),
        unique=True,
        nullable=True
    )

    from_signer_name = db.Column(
        db.String(100),
        nullable=True
    )

    from_signer_position = db.Column(
        db.String(100),
        nullable=True
    )

    to_signer_name = db.Column(
        db.String(100),
        nullable=True
    )

    to_signer_position = db.Column(
        db.String(100),
        nullable=True
    )

    from_signature = db.Column(
        db.Text,
        nullable=True
    )

    to_signature = db.Column(
        db.Text,
        nullable=True
    )

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False
    )

    movement_date = db.Column(
        db.Date,
        nullable=False
    )

    from_location = db.Column(
        db.String(100)
    )

    to_location = db.Column(
        db.String(100)
    )

    from_department = db.Column(
        db.String(100)
    )

    to_department = db.Column(
        db.String(100)
    )

    from_pic = db.Column(
        db.String(100)
    )

    to_pic = db.Column(
        db.String(100)
    )

    reason = db.Column(
        db.String(255)
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime
    )

    asset = db.relationship(
        "Asset",
        back_populates="movements"
    )

# ============================================================
# ASSET MOVEMENT CORRECTION LOG
# ============================================================


class AssetMovementCorrection(db.Model):

    __tablename__ = "asset_movement_corrections"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    movement_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "asset_movements.id"
        ),
        nullable=False
    )

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "assets.id"
        ),
        nullable=False
    )

    # ========================================================
    # WAKTU KOREKSI
    # ========================================================

    corrected_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # ========================================================
    # DATA SEBELUM KOREKSI
    # ========================================================

    old_movement_date = db.Column(
        db.Date,
        nullable=True
    )

    old_from_location = db.Column(
        db.String(100),
        nullable=True
    )

    old_to_location = db.Column(
        db.String(100),
        nullable=True
    )

    old_from_department = db.Column(
        db.String(100),
        nullable=True
    )

    old_to_department = db.Column(
        db.String(100),
        nullable=True
    )

    old_from_pic = db.Column(
        db.String(100),
        nullable=True
    )

    old_to_pic = db.Column(
        db.String(100),
        nullable=True
    )

    old_reason = db.Column(
        db.String(255),
        nullable=True
    )

    old_notes = db.Column(
        db.Text,
        nullable=True
    )

    # ========================================================
    # DATA SESUDAH KOREKSI
    # ========================================================

    new_movement_date = db.Column(
        db.Date,
        nullable=True
    )

    new_from_location = db.Column(
        db.String(100),
        nullable=True
    )

    new_to_location = db.Column(
        db.String(100),
        nullable=True
    )

    new_from_department = db.Column(
        db.String(100),
        nullable=True
    )

    new_to_department = db.Column(
        db.String(100),
        nullable=True
    )

    new_from_pic = db.Column(
        db.String(100),
        nullable=True
    )

    new_to_pic = db.Column(
        db.String(100),
        nullable=True
    )

    new_reason = db.Column(
        db.String(255),
        nullable=True
    )

    new_notes = db.Column(
        db.Text,
        nullable=True
    )

    # ========================================================
    # KETERANGAN KOREKSI
    # ========================================================

    correction_reason = db.Column(
        db.Text,
        nullable=True
    )

    # ========================================================
    # RELATIONSHIP
    # ========================================================

    movement = db.relationship(
        "AssetMovement",
        backref=db.backref(
            "corrections",
            lazy=True
        )
    )

    asset = db.relationship(
        "Asset",
        backref=db.backref(
            "movement_corrections",
            lazy=True
        )
    )

# ============================================================
# COMPANY
# ============================================================


class Company(db.Model):

    __tablename__ = "companies"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    logo = db.Column(
        db.String(255),
        nullable=True
    )

    address = db.Column(
        db.Text,
        nullable=True
    )

    phone = db.Column(
        db.String(50),
        nullable=True
    )

    email = db.Column(
        db.String(150),
        nullable=True
    )

    website = db.Column(
        db.String(200),
        nullable=True
    )

    tax_number = db.Column(
        db.String(100),
        nullable=True
    )

    document_prefix = db.Column(
        db.String(50),
        nullable=True,
        default="MT"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Company {self.name}>"

# ============================================================
# AUDIT LOG
# ============================================================


class AuditLog(db.Model):

    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # user_id sengaja tidak pakai ForeignKey CASCADE ke User -
    # kalau user dihapus, log aktivitasnya harus tetap ada
    # (pakai username yang disimpan terpisah di bawah).
    user_id = db.Column(
        db.Integer,
        nullable=True,
    )

    username = db.Column(
        db.String(50),
        nullable=True,
    )

    action = db.Column(
        db.String(20),
        nullable=False,
    )

    entity_type = db.Column(
        db.String(50),
        nullable=False,
    )

    entity_label = db.Column(
        db.String(200),
        nullable=True,
    )

    description = db.Column(
        db.String(255),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self):
        return (
            f"<AuditLog {self.username} "
            f"{self.action} {self.entity_type}>"
        )

# ============================================================
# ROLE & PERMISSION (MATRIX HAK AKSES)
# ============================================================

# Daftar "object" yang izinnya bisa diatur per role. Manajemen
# User/Role/Menu/Backup/Audit Log sengaja TIDAK masuk daftar ini -
# itu tetap khusus administrator, supaya role custom tidak bisa
# menaikkan hak aksesnya sendiri (privilege escalation).
PERMISSION_OBJECTS = [
    ("asset", "Asset"),
    ("movement", "Mutasi Asset"),
    ("warranty", "Warranty"),
    ("category", "Kategori"),
    ("location", "Lokasi"),
    ("department", "Departemen"),
    ("vendor", "Vendor"),
    ("company", "Company"),
]

PERMISSION_OBJECT_KEYS = [key for key, _label in PERMISSION_OBJECTS]

PERMISSION_ACTIONS = ["create", "read", "edit", "delete"]


class Role(db.Model):

    __tablename__ = "roles"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    description = db.Column(
        db.String(255),
        nullable=True,
    )

    # Role bawaan (administrator) tidak boleh dihapus/diganti nama,
    # supaya selalu ada minimal 1 role dengan akses penuh.
    is_system = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
    )

    permissions = db.relationship(
        "Permission",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    def permission_for(self, object_name):

        for perm in self.permissions:
            if perm.object_name == object_name:
                return perm

        return None

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(db.Model):

    __tablename__ = "permissions"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id"),
        nullable=False,
    )

    object_name = db.Column(
        db.String(50),
        nullable=False,
    )

    can_create = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    can_read = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    can_edit = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    can_delete = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    role = db.relationship(
        "Role",
        back_populates="permissions",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "role_id",
            "object_name",
            name="uq_permission_role_object",
        ),
    )

    def allows(self, action):
        return bool(
            getattr(self, f"can_{action}", False)
        )

    def __repr__(self):
        return (
            f"<Permission role={self.role_id} "
            f"{self.object_name}>"
        )

# ============================================================
# APP SETTING (BRANDING APLIKASI - BUKAN DATA PERUSAHAAN)
# ============================================================


class AppSetting(db.Model):
    """
    Pengaturan tampilan aplikasi itu sendiri (nama, logo, footer,
    halaman login) - beda dengan Company yang isinya data bisnis
    perusahaan untuk kop dokumen. Cuma ada 1 baris (singleton).
    """

    __tablename__ = "app_settings"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    app_name = db.Column(
        db.String(100),
        nullable=False,
        default="Asset Tracker",
    )

    footer_text = db.Column(
        db.String(255),
        nullable=True,
    )

    login_message = db.Column(
        db.String(255),
        nullable=True,
    )

    # Logo lebar/horizontal - dipakai di brand sidebar.
    logo_wide = db.Column(
        db.String(255),
        nullable=True,
    )

    # Logo kotak/square - dipakai di halaman login & favicon.
    logo_square = db.Column(
        db.String(255),
        nullable=True,
    )

    # Cara menampilkan identitas aplikasi di sidebar: "logo_only",
    # "name_only", atau "logo_and_name". Kalau logo belum diupload,
    # semua mode otomatis fallback ke icon + nama aplikasi.
    brand_display_mode = db.Column(
        db.String(20),
        nullable=False,
        default="logo_only",
        server_default="logo_only",
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self):
        return f"<AppSetting {self.app_name}>"
