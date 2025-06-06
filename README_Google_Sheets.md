# Panduan Konfigurasi Integrasi Google Sheets

Template aplikasi AI Marketing Tracker yang Anda berikan (`marketing_tracker_template_adapted.zip`) sudah dilengkapi dengan fitur integrasi Google Sheets. Fitur ini memungkinkan data aplikasi (Aktivitas Pemasaran, Follow-up, Pengguna, Konfigurasi) disinkronkan secara otomatis ke Google Sheets sebagai backup dan dapat dipulihkan kembali.

Berikut adalah langkah-langkah untuk mengaktifkan dan mengkonfigurasi integrasi ini:

## 1. Persiapan Google Sheets dan Service Account

*   **Buat Google Sheet:** Siapkan Google Sheet yang akan digunakan untuk menyimpan data. Pastikan sheet ini memiliki tab (worksheet) dengan nama yang **persis** sama seperti yang diharapkan oleh aplikasi:
    *   `Activities`
    *   `Followups`
    *   `Users`
    *   `Config`
    Struktur kolom pada setiap tab harus sesuai dengan file Excel `MarketingTracker.xlsx` yang Anda berikan atau sesuai dengan definisi header dalam skrip `google_sheets_sync.py`.
*   **Dapatkan Spreadsheet ID:** Salin ID unik dari URL Google Sheet Anda. ID ini adalah string panjang antara `/d/` dan `/edit` di URL. Contoh: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_ANDA/edit`.
*   **Buat Service Account:**
    *   Buka [Google Cloud Console](https://console.cloud.google.com/).
    *   Buat proyek baru atau gunakan proyek yang sudah ada.
    *   Aktifkan **Google Drive API** dan **Google Sheets API** untuk proyek Anda.
    *   Buka menu "IAM & Admin" -> "Service Accounts".
    *   Klik "Create Service Account", berikan nama (misalnya, `marketing-tracker-sync`), dan klik "Create and Continue".
    *   Lewati pemberian peran pada level proyek (klik "Continue").
    *   Klik "Done".
*   **Buat Kunci Service Account:**
    *   Temukan service account yang baru dibuat, klik ikon tiga titik di kolom "Actions", lalu pilih "Manage keys".
    *   Klik "Add Key" -> "Create new key".
    *   Pilih format **JSON** dan klik "Create". File kunci (JSON) akan terunduh secara otomatis. **Simpan file ini dengan aman.**
*   **Bagikan Google Sheet:** Bagikan (Share) Google Sheet Anda dengan alamat email service account yang baru dibuat (terlihat di detail service account, biasanya berakhiran `@<project-id>.iam.gserviceaccount.com`). Berikan akses **Editor**.

## 2. Konfigurasi Aplikasi

*   **Ganti Nama File Kunci:** Ganti nama file JSON kunci yang Anda unduh menjadi `service_account_key.json`.
*   **Tempatkan File Kunci:** Letakkan file `service_account_key.json` ini di direktori utama (root) aplikasi Anda, di tempat yang sama dengan file `app_with_sheets.py`.
*   **(Opsional) Update Spreadsheet ID:**
    *   Buka file `google_sheets_sync.py`.
    *   Cari baris `SPREADSHEET_ID = "1SdEX5TzMzKfKcE1oCuaez2ctxgIxwwipkk9NT0jOYtI"`.
    *   Ganti nilai string tersebut dengan **Spreadsheet ID** Google Sheet Anda yang sebenarnya.
    *   Simpan perubahan.

## 3. Menjalankan dan Menggunakan Integrasi

*   **Jalankan Aplikasi:** Jalankan aplikasi menggunakan skrip `app_with_sheets.py` (misalnya, dengan `streamlit run app_with_sheets.py`).
*   **Akses Fitur Sinkronisasi:**
    *   Login sebagai **superadmin**.
    *   Navigasi ke menu "Pengaturan".
    *   Pilih tab "Google Sheets".
    *   Di sini Anda akan menemukan tombol untuk:
        *   **Sinkronkan Sekarang:** Mendorong data lokal saat ini ke Google Sheets.
        *   **Restore Data:** Memulihkan data dari tab Google Sheets yang dipilih ke aplikasi lokal (hati-hati, ini akan menimpa data lokal).

## Catatan Penting

*   **Keamanan:** Jaga kerahasiaan file `service_account_key.json`. Jangan membagikannya secara publik atau menyimpannya di repositori kode yang tidak aman.
*   **Struktur Data:** Pastikan struktur data (nama sheet dan kolom) di Google Sheets sesuai dengan yang diharapkan aplikasi.
*   **Sinkronisasi:** Skrip `google_sheets_sync.py` saat ini menggunakan metode *append* untuk data aktivitas dan follow-up. Ini berarti jika Anda menjalankan sinkronisasi beberapa kali tanpa membersihkan sheet atau data YAML lokal, data bisa terduplikasi di Google Sheets. Untuk data `Config` dan `Users`, metode *overwrite* digunakan.
*   **Backup Lokal:** Aplikasi juga memiliki fitur backup/restore lokal (di tab "Backup & Restore") yang menyimpan data dalam format YAML di file zip. Integrasi Google Sheets menyediakan lapisan backup tambahan secara online.

Dengan mengikuti langkah-langkah ini, aplikasi Anda akan terintegrasi dengan Google Sheets, memungkinkan backup data yang andal dan pemulihan saat diperlukan.
