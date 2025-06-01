# EMI MARKETING TRACKER 💼📊  
> Aplikasi pencatatan aktivitas pemasaran untuk internal tim EKUITAS MEDIA INVESTAMA (EMI)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)   
[![GitHub issues](https://img.shields.io/github/issues/nusantaraja/MarketingTrackerEMI)](https://github.com/nusantaraja/MarketingTrackerEMI/issues)   
[![Repo Size](https://img.shields.io/github/repo-size/nusantaraja/MarketingTrackerEMI)]()
[![GitHub stars](https://img.shields.io/github/stars/nusantaraja/MarketingTrackerEMI?style=social)](https://github.com/nusantaraja/MarketingTrackerEMI)


---

## 🎯 Deskripsi 

**EMI Marketing Tracker** adalah aplikasi berbasis web sederhana yang membantu tenaga pemasaran dalam mencatat dan mengelola aktivitas harian mereka. Sangat cocok untuk usaha kecil-menengah yang ingin meningkatkan efisiensi proses penjualan dan follow-up calon klien.

Aplikasi ini dibangun menggunakan **Streamlit (Python)** dan mendukung sinkronisasi otomatis ke **Google Sheets**, sehingga data selalu tersimpan aman secara online sebagai backup.

---

## ✅ Fitur Utama

- Input dan manajemen aktivitas pemasaran  
- Catatan follow-up dengan status  
- Manajemen pengguna (Admin & Marketing)  
- Backup & restore data lokal (format YAML)  
- Sinkronisasi otomatis ke **Google Sheets**  
- Pengaturan role-based access control  
- Tampilan responsif dan mudah digunakan  

---

## 🔧 Teknologi yang Digunakan

| Komponen        | Teknologi                |
|----------------|--------------------------|
| Framework      | [Streamlit](https://streamlit.io)  |
| Bahasa Pemrograman | Python 3.x              |
| UI Library     | Streamlit + Bootstrap    |
| Penyimpanan Data | File YAML (lokal), Google Sheets (online) |
| Integrasi      | Google Sheets API        |

---

## 📁 Struktur Direktori
```text
MarketingTrackerEMI/
│
├── app_with_sheets.py       # Main file aplikasi dengan integrasi Google Sheets
├── google_sheets_sync.py    # Modul sinkronisasi ke Google Sheets
├── service_account_key.json # Kunci Service Account Google Cloud (harus diisi)
├── data/                    # Folder penyimpanan data lokal (YAML)
├── LICENSE
└── README.md
```

---

## ⚙️ Cara Konfigurasi Integrasi Google Sheets

### 1. Persiapan Google Sheets

- Buat Google Sheet baru.
- Pastikan sheet memiliki tab:
  - `Activities`
  - `Followups`
  - `Users`
  - `Config`
- Salin **Spreadsheet ID** dari URL Google Sheets (contoh: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`). 

### 2. Setup Service Account

- Buka [Google Cloud Console](https://console.cloud.google.com/) 
- Aktifkan **Google Sheets API** dan **Google Drive API**
- Buat **Service Account**, lalu unduh kunci JSON
- Bagikan Google Sheet dengan email service account (`xxxx@project-id.iam.gserviceaccount.com`)
- Simpan file JSON kunci sebagai `service_account_key.json`

### 3. Letakkan File Kunci

- Taruh file `service_account_key.json` di root direktori proyek, sejajar dengan `app_with_sheets.py`.

### 4. Update Spreadsheet ID (Opsional)

Buka file `google_sheets_sync.py`, ganti baris:

```python
SPREADSHEET_ID = "1SdEX5TzMzKfKcE1oCuaez2ctxgIxwwipkk9NT0jOYtI"
dengan Spreadsheet ID milikmu.
```

▶️ Menjalankan Aplikasi

Pastikan semua dependensi terinstal:

```python
pip install streamlit pandas gspread google-auth pyyaml
```

Lalu jalankan aplikasi:

```
streamlit run app_with_sheets.py
```

Login sebagai superadmin untuk mengakses fitur sinkronisasi dan backup/restore.



🛡️ Keamanan
Jangan upload file service_account_key.json ke repositori publik!
Gunakan .gitignore untuk menyembunyikan file sensitif tersebut.
Selalu pastikan struktur sheet di Google Sheets sesuai dengan yang diharapkan aplikasi.

📄 Lisensi
Proyek ini dilisensikan di bawah MIT License. Lihat file LICENSE untuk detail selengkapnya.

❤️ Terima Kasih
Dibuat dengan ❤️ oleh Tim IT Nusantaraja Group
Jika kamu menyukai proyek ini, jangan ragu untuk star repositori ini atau berkontribusi!