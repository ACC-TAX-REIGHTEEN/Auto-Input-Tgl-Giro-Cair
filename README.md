# 🏦 Auto-Input-Tgl-Giro-Cair

**Sistem Otomatisasi Ekstraksi, Validasi, dan Pencatatan Tanggal Pencairan Bilyet Giro Berbasis Python**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Google Sheets API](https://img.shields.io/badge/Google%20Sheets%20API-v4-34A853?style=for-the-badge&logo=googlesheets&logoColor=white)](https://developers.google.com/sheets/api)
[![ConfigParser](https://img.shields.io/badge/Configuration-.conf%20%7C%20JSON-FFA500?style=for-the-badge)](https://docs.python.org/3/library/configparser.html)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge)]()
[![Maintainer](https://img.shields.io/badge/Maintainer-ihfandica-blue?style=for-the-badge&logo=github)](mailto:me@ihfandica.com)

---

**Auto-Input-Tgl-Giro-Cair** adalah perangkat lunak otomatisasi alur kerja (*workflow automation*) finansial dan akuntansi yang dirancang untuk mengeliminasi proses manual dalam pengecekan serta penginputan tanggal pencairan bilyet giro. Proyek ini memisahkan logika kerja ke dalam arsitektur dua tahap (*Two-Stage ETL Pipeline*) di dalam modul `Dapur/`—yakni penarikan data (`1_TarikData.py`) serta validasi dan penulisan balik (`2_CekData&Tulis.py`)—yang dikendalikan secara terpusat melalui satu skrip eksekutor (`Jalankan Program.py`).

---

## 📑 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Arsitektur & Alur Kerja](#-arsitektur--alur-kerja)
- [Teknologi yang Digunakan](#-teknologi-yang-digunakan)
- [Struktur Direktori](#-struktur-direktori)
- [Prasyarat Sistem](#-prasyarat-sistem)
- [Panduan Instalasi & Konfigurasi](#-panduan-instalasi--konfigurasi)
- [Cara Penggunaan](#-cara-penggunaan)
- [Referensi Konfigurasi](#-referensi-konfigurasi)
- [Penanganan Masalah Umum (Troubleshooting)](#-penanganan-masalah-umum-troubleshooting)
- [Kontribusi & Lisensi](#-kontribusi--lisensi)

---

## ✨ Fitur Utama

1. **Orkestrasi Satu Pintu (`Jalankan Program.py`)**  
   Menyediakan *single entry point* yang mengeksekusi seluruh rangkaian pipeline dari hulu ke hilir secara otomatis tanpa perlu menjalankan skrip satu per satu.
2. **Ekstraksi Data Terotomasi (`Dapur/1_TarikData.py`)**  
   Menghubungkan sistem ke sumber data eksternal (Google Sheets / basis data mutasi) menggunakan autentikasi `credentials.json` untuk menarik daftar bilyet giro dan data pencairan terbaru.
3. **Rekonsiliasi & Penulisan Otomatis (`Dapur/2_CekData&Tulis.py`)**  
   Melakukan pencocokan (*matching*) nomor giro, memverifikasi status pencairan, dan menginput tanggal giro cair secara presisi pada baris serta kolom lembar kerja target.
4. **Konfigurasi Eksternal Terpisah (`Dapur/config.conf`)**  
   Memisahkan parameter operasional (ID dokumen, nama *sheet*/lembar kerja, rentang kolom, dan pengaturan lokal) dari kode sumber Python sehingga perubahan parameter tidak memerlukan modifikasi kode (*zero hardcoding*).
5. **Isolasi Kredensial Keamanan (`Dapur/credentials.json`)**  
   Menggunakan berkas kredensial JSON terpisah yang secara bawaan diisi dengan penanda `# dummy` pada repositori publik guna mencegah kebocoran kunci rahasia (*secret leakage*).

---

## 🔄 Arsitektur & Alur Kerja

Sistem bekerja menggunakan pendekatan *modular pipeline* yang mengisolasi proses pembacaan data dari proses manipulasi/penulisan data:

```text
+-----------------------------------------------------------------------+
|                        Jalankan Program.py                            |
|                  (Main Orchestrator / Entry Point)                    |
+-----------------------------------+-----------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v (Tahap 1)                                           v (Tahap 2)
+------------------------+                           +--------------------------+
|  Dapur/1_TarikData.py  |                           | Dapur/2_CekData&Tulis.py |
|  (Data Extraction)     |                           | (Validation & Write-back)|
+-----------+------------+                           +------------+-------------+
            |                                                     ^
            | Membaca Konfigurasi & Autentikasi                   |
            +-----------------------+-----------------------------+
                                    |
                                    v
            +-----------------------------------------------+
            |  Dapur/config.conf  &  Dapur/credentials.json |
            +-----------------------+-----------------------+
                                    |
                                    v
        +-------------------------------------------------------+
        |         Sumber Data / Google Sheets API               |
        | 1. Ambil daftar nomor giro & mutasi bank              |
        | 2. Bandingkan status giro yang belum memiliki tanggal |
        | 3. Tulis otomatis Tanggal Giro Cair ke kolom target   |
        +-------------------------------------------------------+
```

---

## 🛠️ Teknologi yang Digunakan

| Komponen | Teknologi / Pustaka | Peran dalam Sistem |
| :--- | :--- | :--- |
| **Bahasa Pemrograman** | Python 3.8+ | Runtime utama untuk eksekusi orkestrator dan modul pemrosesan data. |
| **Manajemen Konfigurasi** | `configparser` / `.conf` | Membaca parameter lingkungan dan referensi tabel dari `Dapur/config.conf`. |
| **Autentikasi API** | `google-auth` / `oauth2client` | Mengelola autentikasi Service Account menggunakan berkas `Dapur/credentials.json`. |
| **Integrasi Spreadsheet** | `gspread` / Google API Client | Menangani operasi baca (*fetch*) pada `1_TarikData.py` dan tulis (*update*) pada `2_CekData&Tulis.py`. |
| **Pemrosesan Data** | `pandas` / Standard Library | Melakukan pencocokan silang (*cross-checking*), pemfilteran, dan pemformatan tanggal giro cair. |

---

## 📂 Struktur Direktori

Berikut adalah struktur berkas di dalam repositori beserta fungsi masing-masing komponen:

```text
Auto-Input-Tgl-Giro-Cair-main/
├── Dapur/                        # Paket inti (backend engine) dan penyimpanan konfigurasi
│   ├── __init__.py               # Inisialisasi paket Python Dapur (metadata: me@ihfandica.com)
│   ├── 1_TarikData.py            # Modul Tahap 1: Penarikan dan ekstraksi data sumber
│   ├── 2_CekData&Tulis.py        # Modul Tahap 2: Validasi pencairan giro & input tanggal otomatis
│   ├── config.conf               # Berkas konfigurasi parameter spreadsheet, sheet, dan kolom
│   └── credentials.json          # Kredensial Google Service Account (default: "# dummy")
└── Jalankan Program.py           # Skrip utama (entry point) untuk menjalankan seluruh alur kerja
```

---

## 📋 Prasyarat Sistem

Sebelum menginstal dan menjalankan program, pastikan lingkungan sistem Anda memenuhi prasyarat berikut:

1. **Python**: Versi `3.8` atau yang lebih baru telah terinstal dan ditambahkan ke dalam `PATH` sistem operasi.
2. **Akun Google Cloud Platform (GCP)**:
   - Proyek GCP dengan **Google Sheets API** dan **Google Drive API** yang telah diaktifkan (*enabled*).
   - Kunci **Service Account** dalam format JSON.
3. **Akses Lembar Kerja (Spreadsheet)**:
   - Alamat email Service Account (`client_email` di dalam `credentials.json`) **wajib diberikan akses Editor** pada dokumen Google Sheets target.
4. **Koneksi Internet Stabil**: Diperlukan untuk komunikasi API saat menarik dan menulis data secara *real-time*.

---

## 🚀 Panduan Instalasi & Konfigurasi

Ikuti langkah-langkah berikut secara berurutan untuk menyiapkan proyek:

### 1. Kloning Repositori

```bash
git clone https://github.com/ACC-TAX-REIGHTEEN/Auto-Input-Tgl-Giro-Cair.git
cd Auto-Input-Tgl-Giro-Cair
```

### 2. Buat dan Aktifkan Virtual Environment (Direkomendasikan)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalasi Dependensi Pustaka

Instal pustaka Python yang dibutuhkan:

```bash
pip install --upgrade pip
pip install gspread google-auth google-auth-oauthlib pandas configparser requests
```

### 4. Konfigurasi Kredensial (`Dapur/credentials.json`)

Secara bawaan, berkas `Dapur/credentials.json` hanya berisi teks `# dummy`. Ganti seluruh isinya dengan kredensial JSON asli dari Google Cloud Service Account Anda:

```json
{
  "type": "service_account",
  "project_id": "nama-proyek-gcp-anda",
  "private_key_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "bot-giro@nama-proyek-gcp-anda.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

> ⚠️ **Penting:** Jangan pernah mengunggah berkas `Dapur/credentials.json` yang berisi kunci asli ke repositori publik.

### 5. Sesuaikan Parameter pada `Dapur/config.conf`

Buka berkas `Dapur/config.conf` menggunakan text editor dan sesuaikan ID Spreadsheet, nama sheet/tab, serta pemetaan kolom dengan tabel operasional Anda.

---

## 💻 Cara Penggunaan

### Eksekusi Otomatis Penuh (Direkomendasikan)

Jalankan skrip utama dari direktori akar proyek:

```bash
python "Jalankan Program.py"
```

Skrip ini akan secara otomatis:
1. Menjalankan `Dapur/1_TarikData.py` untuk mengambil data mutasi/giro.
2. Menjalankan `Dapur/2_CekData&Tulis.py` untuk memvalidasi dan menuliskan tanggal pencairan ke lembar kerja.

### Eksekusi Modular (Per Tahap)

**Tahap 1 — Hanya Menarik Data:**
```bash
python Dapur/1_TarikData.py
```

**Tahap 2 — Hanya Mengecek dan Menulis Data:**
```bash
python "Dapur/2_CekData&Tulis.py"
```

---

## ⚙️ Referensi Konfigurasi

| Berkas | Kategori | Deskripsi |
| :--- | :--- | :--- |
| `Dapur/config.conf` | **Konfigurasi Sumber & Target** | Menyimpan ID Spreadsheet, nama lembar kerja (*worksheet*), serta indeks kolom target. |
| `Dapur/credentials.json` | **Kredensial API** | Berisi kunci privat Service Account untuk otentikasi bot Google Sheets API. |

---

## 🔧 Penanganan Masalah Umum (Troubleshooting)

### 1. `json.decoder.JSONDecodeError`
- **Penyebab**: Berkas `Dapur/credentials.json` masih berisi teks `# dummy` atau JSON rusak.
- **Solusi**: Tempelkan JSON Service Account yang valid dari Google Cloud Console.

### 2. `gspread.exceptions.APIError: [403] The caller does not have permission`
- **Penyebab**: Email Service Account belum diberikan akses Editor pada Spreadsheet.
- **Solusi**: Salin `client_email` dari `credentials.json` dan bagikan (*share*) spreadsheet tersebut dengan hak akses **Editor**.

### 3. `FileNotFoundError: [Errno 2] No such file or directory: 'Dapur/...'`
- **Penyebab**: Terminal tidak berada di direktori akar proyek saat menjalankan perintah.
- **Solusi**: Pastikan terminal berada di folder utama (`Auto-Input-Tgl-Giro-Cair-main/`) sebelum mengeksekusi skrip.

---

## 📜 Lisensi

Proyek ini dikembangkan untuk keperluan internal perusahaan. Silakan sesuaikan dengan kebutuhan organisasi Anda.

---

*Dikembangkan oleh [ACC-TAX-REIGHTEEN](https://github.com/ACC-TAX-REIGHTEEN)*
