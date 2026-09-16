"""
Menjalankan Asset Tracker dengan WSGI server produksi (waitress),
bukan development server Flask.

Development server Flask (run.py, debug=True) TIDAK aman dipakai
selain di komputer sendiri untuk coding - debugger bawaannya bisa
dipakai orang lain untuk menjalankan kode sembarang di server kalau
aplikasi ini bisa diakses dari luar (jaringan kantor/internet).

Cara pakai:
    python serve_production.py

Secara default listen di semua network interface (0.0.0.0) port 8000,
supaya bisa diakses komputer lain di jaringan yang sama. Ubah HOST/PORT
di bawah kalau perlu.
"""

from waitress import serve

from app import create_app


HOST = "192.168.120.229"
PORT = 8000

app = create_app()

app.config["DEBUG"] = False


if __name__ == "__main__":

    print(f"Asset Tracker berjalan di http://{HOST}:{PORT}")
    print("(atau http://<ip-komputer-ini>:8000 dari komputer lain di jaringan yang sama)")

    serve(
        app,
        host=HOST,
        port=PORT,
        threads=4,
    )
