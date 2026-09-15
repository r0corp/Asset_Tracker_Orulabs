import sqlite3

conn = sqlite3.connect("instance/asset.db")
cursor = conn.cursor()

rows = cursor.execute("""
    SELECT
        asset_id,
        id,
        movement_no,
        movement_date,
        from_location,
        to_location,
        from_department,
        to_department,
        from_pic,
        to_pic
    FROM asset_movements
    ORDER BY
        asset_id,
        movement_date,
        id
""").fetchall()

previous = {}
errors = []

for row in rows:

    (
        asset_id,
        movement_id,
        movement_no,
        movement_date,
        from_location,
        to_location,
        from_department,
        to_department,
        from_pic,
        to_pic,
    ) = row

    # Movement pertama untuk asset tidak perlu dibandingkan
    if asset_id in previous:

        prev_location, prev_department, prev_pic = previous[asset_id]

        # CHECK LOCATION
        if prev_location != (from_location or ""):
            errors.append({
                "asset_id": asset_id,
                "movement_id": movement_id,
                "movement_no": movement_no,
                "type": "LOCATION",
                "previous_to": prev_location,
                "current_from": from_location or "",
            })

        # CHECK DEPARTMENT
        if prev_department != (from_department or ""):
            errors.append({
                "asset_id": asset_id,
                "movement_id": movement_id,
                "movement_no": movement_no,
                "type": "DEPARTMENT",
                "previous_to": prev_department,
                "current_from": from_department or "",
            })

        # CHECK PIC
        if prev_pic != (from_pic or ""):
            errors.append({
                "asset_id": asset_id,
                "movement_id": movement_id,
                "movement_no": movement_no,
                "type": "PIC",
                "previous_to": prev_pic,
                "current_from": from_pic or "",
            })

    # Simpan TO movement sekarang
    # sebagai FROM movement berikutnya
    previous[asset_id] = (
        to_location or "",
        to_department or "",
        to_pic or "",
    )


print()
print("=" * 70)
print("HASIL PEMERIKSAAN URUTAN MOVEMENT")
print("=" * 70)

print()
print(f"Total movement : {len(rows)}")
print(f"Total error    : {len(errors)}")
print()

if not errors:

    print("✓ SEMUA MOVEMENT KONSISTEN")
    print()
    print(
        "TO movement sebelumnya = FROM movement berikutnya."
    )

else:

    print("✗ DITEMUKAN MOVEMENT YANG TIDAK KONSISTEN")
    print()

    for error in errors:

        print(
            f"Asset ID       : {error['asset_id']}"
        )

        print(
            f"Movement       : {error['movement_no']}"
        )

        print(
            f"Jenis          : {error['type']}"
        )

        print(
            f"Previous TO    : {error['previous_to']}"
        )

        print(
            f"Current FROM   : {error['current_from']}"
        )

        print("-" * 70)

conn.close()
