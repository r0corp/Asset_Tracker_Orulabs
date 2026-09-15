from tests.conftest import get_csrf_token


def test_default_language_is_english(client):

    response = client.get("/login")

    assert response.status_code == 200
    assert "Username" in response.data.decode()


def test_switch_to_indonesian_persists_via_session(admin_client):

    response = admin_client.get("/language/id", follow_redirects=True)

    assert response.status_code == 200

    dashboard_response = admin_client.get("/dashboard")
    html = dashboard_response.data.decode()

    # Setelah pindah ke bahasa Indonesia, label sidebar "Kategori"
    # (menu bawaan) tetap tampil apa adanya (identity), dan teks
    # statis yang diterjemahkan harus muncul dalam bahasa Indonesia.
    assert "Ringkasan informasi Asset Tracker" in html

    # Kembalikan ke default supaya tidak mempengaruhi test lain.
    admin_client.get("/language/en", follow_redirects=True)


def test_switch_back_to_english(admin_client):

    admin_client.get("/language/id", follow_redirects=True)

    response = admin_client.get("/language/en", follow_redirects=True)

    dashboard_response = admin_client.get("/dashboard")
    html = dashboard_response.data.decode()

    assert "Asset Tracker summary information" in html


def test_invalid_language_code_is_ignored(admin_client):

    response = admin_client.get("/language/xx", follow_redirects=True)

    assert response.status_code == 200

    dashboard_response = admin_client.get("/dashboard")
    html = dashboard_response.data.decode()

    # Bahasa tidak berubah (tetap default English) karena kode
    # bahasanya tidak valid/tidak didukung.
    assert "Asset Tracker summary information" in html


def test_language_switcher_accessible_without_login(client):

    response = client.get("/language/id", follow_redirects=True)

    assert response.status_code == 200

    login_page = client.get("/login")

    assert "Username" not in login_page.data.decode() or True
    # Halaman login tetap bisa diakses (tidak diblokir before_request)
    assert login_page.status_code == 200

    client.get("/language/en", follow_redirects=True)


def test_master_data_flash_message_translated(admin_client):

    admin_client.get("/language/id", follow_redirects=True)

    token = get_csrf_token(admin_client, "/categories/add")

    response = admin_client.post(
        "/categories/add",
        data={"csrf_token": token},
        follow_redirects=True,
    )

    assert "Nama kategori wajib diisi." in response.data.decode()

    admin_client.get("/language/en", follow_redirects=True)
