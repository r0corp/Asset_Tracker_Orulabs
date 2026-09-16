"""Daftar label menu sidebar yang tersimpan di tabel `menu_items`.

Label menu diterjemahkan secara dinamis lewat `_(entry.item.label)` di
`base.html` - karena nilainya datang dari database, bukan string literal
di kode, `pybabel extract` tidak bisa menemukannya secara otomatis dan
entrinya akan ditandai usang (obsolete) lalu hilang dari katalog setiap
kali `pybabel update` dijalankan (ini yang membuat menu "Settings" tidak
ikut berubah saat bahasa diganti). File ini hanya berisi pemanggilan
literal `_(...)` supaya babel selalu menemukan & mempertahankan semua
label menu baku di katalog terjemahan. File ini tidak pernah diimpor
atau dijalankan oleh aplikasi.
"""

from flask_babel import gettext as _

_("Dashboard")
_("Asset")
_("Master Data")
_("Category")
_("Location")
_("Department")
_("Vendor")
_("Company")
_("Movement Report")
_("Warranty")
_("Audit Log")
_("Backup Database")
_("Clear Cache")
_("User Management")
_("Role Management")
_("Menu Management")
_("Settings")
_("Application Settings")
_("Pemisah")
