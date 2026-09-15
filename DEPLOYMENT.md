# Deployment Guide — 1 PC Sebagai Server

Panduan ini untuk memindahkan Asset Tracker ke 1 PC Windows terpisah yang
akan dijadikan server, diakses oleh komputer lain di jaringan kantor
(LAN) lewat browser.

Asumsi: PC server pakai Windows, dan aplikasi hanya perlu diakses dari
dalam jaringan kantor (bukan dari internet). Kalau nanti butuh diakses
dari luar juga, lihat bagian **HTTPS & Akses dari Luar** di paling bawah.

---

## 1. Siapkan PC Server

- Install **Python 3.10 atau lebih baru** dari https://python.org (saat
  install, centang "Add Python to PATH").
- **Matikan Sleep/Hibernate**: Settings → System → Power → ubah "Sleep"
  jadi "Never". PC ini harus tetap nyala 24/7 supaya aplikasi selalu
  bisa diakses.
- **Set IP tetap** supaya alamat aplikasi tidak berubah-ubah:
  - Cara termudah: reservasi IP di router/DHCP server kantor berdasarkan
    MAC address PC ini (tanya ke yang kelola jaringan kalau bukan Anda
    sendiri).
  - Cek IP dan MAC address PC ini dengan `ipconfig /all` di Command
    Prompt.

## 2. Pindahkan Project

Copy seluruh folder project ini ke PC server, misalnya ke
`C:\AssetTracker`. **Jangan ikut copy** folder `venv/`, `__pycache__/`,
dan file `instance/asset.db` (biarkan database dibuat baru dan kosong
di server — lihat langkah 4).

## 3. Install Dependencies

Buka Command Prompt / PowerShell di folder project (`C:\AssetTracker`):

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Konfigurasi `.env`

Buat file `.env` baru di folder project (**jangan copy `.env` dari
komputer development** — harus pakai `SECRET_KEY` baru yang berbeda).
Generate `SECRET_KEY` acak:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Isi `.env`:

```
SECRET_KEY=<hasil generate di atas>
```

## 5. Setup Database (sekali saja, saat pertama kali)

```bash
python -m flask --app run.py db upgrade
python seed_admin.py
python seed_roles.py
python seed_menu.py
```

`seed_admin.py` akan membuat akun admin pertama — catat username/password
yang ditampilkan, lalu **segera login dan ganti passwordnya**.

## 6. Buka Windows Firewall

Supaya PC lain di jaringan bisa akses port aplikasi (default 8000):

```powershell
netsh advfirewall firewall add rule name="Asset Tracker" dir=in action=allow protocol=TCP localport=8000
```

## 7. Jalankan Sebagai Windows Service (auto-start & auto-restart)

Supaya aplikasi otomatis jalan saat PC nyala/restart, dan tidak perlu ada
yang login terus-terusan di PC tersebut, pakai
[NSSM](https://nssm.cc/download) (Non-Sucking Service Manager):

1. Download NSSM, extract, lalu copy `nssm.exe` (versi 64-bit, di folder
   `win64`) ke `C:\AssetTracker\nssm.exe`.
2. Install service (jalankan sebagai Administrator):

```powershell
nssm install AssetTracker "C:\AssetTracker\venv\Scripts\python.exe" "C:\AssetTracker\serve_production.py"
nssm set AssetTracker AppDirectory "C:\AssetTracker"
nssm set AssetTracker Start SERVICE_AUTO_START
nssm start AssetTracker
```

3. Cek statusnya: `nssm status AssetTracker` (harus `SERVICE_RUNNING`).
   Untuk stop/restart: `nssm stop AssetTracker` / `nssm restart AssetTracker`.

Kalau tidak mau pakai NSSM, alternatif paling sederhana: buat shortcut ke
`serve_production.py` di folder Startup Windows — tapi ini butuh ada user
yang login ke PC, dan tidak auto-restart kalau aplikasinya crash.

## 8. Test Akses

Dari PC server sendiri: `http://localhost:8000`

Dari PC lain di jaringan yang sama: `http://<ip-pc-server>:8000`
(pakai IP dari langkah 1).

## 9. Backup Otomatis ke Lokasi Lain

Aplikasi sudah punya fitur Backup Database (menu Backup Database →
Create New Backup), tapi file backup-nya tersimpan di folder `backups/`
di PC server yang sama — kalau PC/disk itu rusak, backup ikut hilang.
Sebaiknya jadwalkan salinan otomatis ke lokasi lain (network drive,
external drive, atau cloud storage) pakai Task Scheduler, misalnya
script yang menjalankan:

```powershell
robocopy "C:\AssetTracker\backups" "\\NAS\backup-assettracker" /MIR
```

dijadwalkan harian di luar jam kerja.

## 10. Update Aplikasi di Kemudian Hari

Kalau ada perubahan kode yang perlu diterapkan ke server:

```powershell
nssm stop AssetTracker
:: copy file yang berubah ke C:\AssetTracker
venv\Scripts\activate
python -m flask --app run.py db upgrade   :: kalau ada migration baru
nssm start AssetTracker
```

---

## HTTPS & Akses dari Luar (opsional)

Kalau nanti aplikasi juga perlu diakses dari luar jaringan kantor
(misalnya WFH lewat internet), **jangan** expose port 8000 langsung ke
internet. Pasang reverse proxy (IIS dengan URL Rewrite, atau nginx) di
depan waitress: reverse proxy terima koneksi HTTPS di port 443 dengan
sertifikat TLS, lalu diteruskan ke `localhost:8000`. Ini di luar cakupan
panduan ini — tanya lagi kalau sudah sampai tahap itu.
