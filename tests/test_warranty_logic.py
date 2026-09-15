from datetime import date

from app.blueprints.helpers import calculate_warranty_end_date, get_warranty_status


def test_calculate_warranty_end_date_years():

    result = calculate_warranty_end_date(
        date(2024, 1, 15),
        "2 Tahun",
    )

    assert result == date(2026, 1, 15)


def test_calculate_warranty_end_date_months():

    result = calculate_warranty_end_date(
        date(2026, 1, 31),
        "1 Bulan",
    )

    # 31 Januari + 1 bulan -> Februari cuma sampai tanggal 28/29
    assert result == date(2026, 2, 28)


def test_calculate_warranty_end_date_no_purchase_date():

    assert calculate_warranty_end_date(None, "1 Tahun") is None


def test_calculate_warranty_end_date_unrecognized_unit():

    assert calculate_warranty_end_date(date(2026, 1, 1), "seumur hidup") is None


def test_get_warranty_status_active():

    result = get_warranty_status(
        date(2026, 1, 1),
        "2 Tahun",
        today=date(2026, 6, 1),
    )

    assert result["status"] == "active"
    assert result["days_left"] > 30


def test_get_warranty_status_expiring_soon():

    result = get_warranty_status(
        date(2026, 1, 1),
        "6 Bulan",
        today=date(2026, 6, 25),
    )

    assert result["status"] == "expiring"
    assert 0 <= result["days_left"] <= 30


def test_get_warranty_status_expired():

    result = get_warranty_status(
        date(2020, 1, 1),
        "1 Tahun",
        today=date(2026, 1, 1),
    )

    assert result["status"] == "expired"
    assert result["days_left"] < 0


def test_get_warranty_status_unknown_when_no_warranty_info():

    result = get_warranty_status(None, None)

    assert result["status"] == "unknown"
    assert result["end_date"] is None
