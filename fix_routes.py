from pathlib import Path
import re

routes = Path("app/routes.py.backup")
target = Path("app/routes.py")

text = routes.read_text(encoding="utf-8")

# ------------------------------------------------------------
# FIX ROUTE ASSET DETAIL
# ------------------------------------------------------------

text = re.sub(
    r'@main\.route\("/assets/(?:int:)?asset_id"\)\s*'
    r'def asset_detail\(asset_id\):',
    '@main.route("/assets/<int:asset_id>")\n'
    'def asset_detail(asset_id):',
    text
)

# ------------------------------------------------------------
# FIX ROUTE EDIT ASSET
# ------------------------------------------------------------

text = re.sub(
    r'@main\.route\(\s*'
    r'"/assets/(?:int:)?asset_id/edit",\s*'
    r'methods=\["GET", "POST"\]\s*'
    r'\)\s*'
    r'def edit_asset\(asset_id\):',
    '@main.route(\n'
    '    "/assets/<int:asset_id>/edit",\n'
    '    methods=["GET", "POST"]\n'
    ')\n'
    'def edit_asset(asset_id):',
    text
)

# ------------------------------------------------------------
# FIX TEMPLATE PARAMETER REFERENCES
# ------------------------------------------------------------

templates = [
    Path("app/templates/asset/list.html"),
    Path("app/templates/asset/detail.html"),
    Path("app/templates/asset/edit.html"),
    Path("app/templates/dashboard.html"),
    Path("app/templates/asset/labels.html"),
    Path("app/templates/asset/labels_select.html"),
    Path("app/templates/asset/import_result.html"),
]

for path in templates:

    if not path.exists():
        continue

    content = path.read_text(encoding="utf-8")

    # asset_detail
    content = re.sub(
        r"('main\.asset_detail'\s*,\s*)id\s*=",
        r"\1asset_id=",
        content
    )

    # edit_asset
    content = re.sub(
        r"('main\.edit_asset'\s*,\s*)id\s*=",
        r"\1asset_id=",
        content
    )

    # direct simple forms
    content = content.replace(
        "main.asset_detail', id=asset.id",
        "main.asset_detail', asset_id=asset.id"
    )

    content = content.replace(
        "main.edit_asset', id=asset.id",
        "main.edit_asset', asset_id=asset.id"
    )

    path.write_text(content, encoding="utf-8")

# ------------------------------------------------------------
# SAVE ROUTES
# ------------------------------------------------------------

target.write_text(text, encoding="utf-8")

print("")
print("==============================================")
print(" ROUTES BERHASIL DIPULIHKAN DAN DIPERBAIKI")
print("==============================================")
print("")
print("routes.py dibuat dari routes.py.backup")
print("Route asset_detail diperbaiki")
print("Route edit_asset diperbaiki")
print("Template asset_detail diperbaiki")
print("Template edit_asset diperbaiki")
print("")
