# Panduan Menggunakan Streamlit Secrets untuk Kredensial Google Sheets

Saat men-deploy aplikasi ke Streamlit Cloud, sangat penting untuk tidak menyimpan file kredensial sensitif seperti `service_account_key.json` langsung di dalam repository GitHub Anda karena alasan keamanan.

Streamlit Cloud menyediakan fitur "Secrets" untuk menyimpan informasi sensitif ini dengan aman.

## Langkah-langkah Menggunakan Secrets:

1.  **Siapkan Konten Kredensial:** Buka file `service_account_key.json` Anda. Anda akan membutuhkan seluruh konten JSON di dalamnya.

2.  **Format Secret dalam TOML:** Buat format TOML (Tom's Obvious, Minimal Language) untuk secret Anda. Struktur ini akan dimasukkan ke dalam pengaturan Secrets di Streamlit Cloud. Contoh formatnya:

    ```toml
    # .streamlit/secrets.toml
    [google_credentials]
    type = "service_account"
    project_id = "<YOUR_PROJECT_ID>"
    private_key_id = "<YOUR_PRIVATE_KEY_ID>"
    private_key = "-----BEGIN PRIVATE KEY-----\n<YOUR_PRIVATE_KEY_LINE_1>\n<YOUR_PRIVATE_KEY_LINE_2>\n...\n-----END PRIVATE KEY-----\n"
    client_email = "<YOUR_SERVICE_ACCOUNT_EMAIL>"
    client_id = "<YOUR_CLIENT_ID>"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/<YOUR_SERVICE_ACCOUNT_EMAIL_ENCODED>"
    universe_domain = "googleapis.com"
    ```

    **Penting:**
    *   Ganti semua nilai `<...>` dengan nilai yang sesuai dari file `service_account_key.json` Anda.
    *   Untuk `private_key`, pastikan Anda mempertahankan karakter newline (`\n`) persis seperti yang ada di file JSON. Kunci privat harus diapit oleh tanda kutip tiga (`"""`) atau tanda kutip tunggal (`'''`) jika Anda menyimpannya dalam file `.streamlit/secrets.toml` lokal, tetapi saat menempelkannya langsung ke UI Streamlit Cloud, gunakan format di atas dalam satu blok teks.

3.  **Tambahkan Secret di Streamlit Cloud:**
    *   Buka aplikasi Anda di Streamlit Cloud.
    *   Klik "Settings".
    *   Scroll ke bagian "Secrets".
    *   Salin dan tempel seluruh blok TOML yang telah Anda format di atas ke dalam editor Secrets.
    *   Klik "Save".

4.  **Modifikasi Kode Aplikasi:** Anda perlu memperbarui kode Python (`google_sheets_sync.py`) untuk membaca kredensial dari Streamlit Secrets saat di-deploy, dan tetap bisa membaca dari file lokal saat dijalankan di komputer Anda.

    Saya akan menyediakan file `google_sheets_sync.py` yang sudah dimodifikasi untuk ini.
