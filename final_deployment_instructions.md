# Panduan Deployment Akhir ke Streamlit Cloud

Berikut adalah ringkasan langkah-langkah untuk men-deploy aplikasi Marketing Tracker Anda ke Streamlit Cloud, menggabungkan panduan sebelumnya dan penanganan kredensial yang aman:

**1. Persiapan Kode & Repository:**

*   **Ganti File Sync:** Ganti file `google_sheets_sync.py` yang ada di proyek Anda dengan file `google_sheets_sync_secrets.py` yang baru saja saya buat. Anda bisa menghapus file lama dan mengganti nama file baru menjadi `google_sheets_sync.py`.
    *   File baru ini sudah dimodifikasi untuk membaca kredensial Google dari Streamlit Secrets saat di-deploy, dan dari file lokal (`service_account_key.json`) saat dijalankan di komputer Anda.
*   **Pastikan `.gitignore`:** Pastikan file `service_account_key.json` **tidak** akan ter-commit ke GitHub. Tambahkan baris berikut ke file `.gitignore` Anda jika belum ada:
    ```
    service_account_key.json
    ```
*   **Commit & Push:** Commit semua perubahan terbaru (termasuk `google_sheets_sync.py` yang baru dan `.gitignore`) ke repository GitHub Anda.

**2. Konfigurasi Streamlit Secrets (PENTING):**

*   **Jangan Upload File Kunci:** Jangan pernah meng-upload file `service_account_key.json` ke GitHub.
*   **Gunakan Secrets:** Ikuti panduan di file `streamlit_secrets_guide.md` (terlampir) untuk menyalin konten dari `service_account_key.json` Anda dan menambahkannya sebagai secret di pengaturan aplikasi Streamlit Cloud Anda dengan format TOML yang benar.

**3. Deploy di Streamlit Cloud:**

*   Login ke [Streamlit Cloud](https://streamlit.io/cloud).
*   Klik "New app".
*   Pilih repository GitHub Anda dan branch `main`.
*   Pada bagian "Main file path", pastikan Anda memasukkan nama file utama aplikasi Anda, yaitu: `app_with_sheets.py`.
*   Klik "Deploy!".

**4. Verifikasi:**

*   Setelah deployment selesai, buka aplikasi Anda melalui URL yang disediakan Streamlit Cloud.
*   Aplikasi seharusnya sekarang dapat terhubung ke Google Sheets menggunakan kredensial yang disimpan di Secrets.
*   Coba tambahkan data baru dan periksa apakah data tersebut muncul di Google Sheet Anda.

**File Pendukung:**

*   `streamlit_secrets_guide.md`: Panduan detail format dan cara menambahkan Google Credentials ke Streamlit Secrets.
*   `deployment_guide_revised.md`: Panduan umum deployment (referensi).
*   Kode aplikasi terbaru (dalam file zip terlampir di pesan berikutnya).

Jika Anda mengikuti langkah-langkah ini, aplikasi Anda seharusnya berjalan di Streamlit Cloud dengan aman dan terhubung ke Google Sheets.
