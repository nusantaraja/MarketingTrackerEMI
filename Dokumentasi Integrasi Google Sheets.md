# Dokumentasi Integrasi Google Sheets

## Fitur Integrasi Google Sheets

Aplikasi AI Marketing Tracker sekarang terintegrasi dengan Google Sheets untuk menyimpan dan memulihkan data secara otomatis. Fitur ini memastikan data aktivitas pemasaran tetap tersimpan aman dan dapat dipulihkan jika terjadi masalah.

### Fitur Utama

1. **Sinkronisasi Otomatis**
   - Data secara otomatis disinkronkan ke Google Sheets setiap kali ada perubahan
   - Semua data (aktivitas pemasaran, follow-up, pengguna, konfigurasi) disinkronkan

2. **Rotasi Tab Bulanan**
   - Setiap bulan, tab baru dibuat di Google Sheets dengan format nama `YYYY_MM`
   - Data disimpan di tab sesuai dengan bulan saat ini

3. **Backup dan Restore**
   - Google Sheets berfungsi sebagai backup data dan sumber untuk pemulihan
   - Fitur restore memungkinkan pemulihan data dari tab Google Sheets tertentu

4. **Antarmuka Pengguna**
   - Tab "Google Sheets" di halaman Pengaturan untuk manajemen sinkronisasi
   - Tombol untuk sinkronisasi manual dan restore data

### Keterbatasan

- Sinkronisasi terjadwal secara periodik saat ini tidak tersedia
- Untuk memastikan data selalu tersinkronisasi, gunakan tombol "Sinkronkan Sekarang" secara manual

## Cara Penggunaan

### Sinkronisasi Manual

1. Buka aplikasi dan login sebagai superadmin
2. Navigasi ke menu "Pengaturan"
3. Pilih tab "Google Sheets"
4. Klik tombol "Sinkronkan Sekarang" untuk memulai sinkronisasi manual

### Restore Data

1. Buka aplikasi dan login sebagai superadmin
2. Navigasi ke menu "Pengaturan"
3. Pilih tab "Google Sheets"
4. Pilih tab yang ingin dipulihkan dari dropdown
5. Klik tombol "Restore Data"
6. Centang kotak konfirmasi
7. Data akan dipulihkan dari Google Sheets ke aplikasi lokal

## Struktur Data di Google Sheets

Setiap tab bulanan di Google Sheets berisi semua data aplikasi dengan format berikut:

1. **Marketing Activities**
   - Semua data aktivitas pemasaran dengan kolom ID, nama prospek, lokasi, dll.

2. **Followups**
   - Semua data follow-up dengan kolom ID, ID aktivitas, catatan, tindakan selanjutnya, dll.

3. **Users**
   - Data pengguna aplikasi dengan kolom username, nama, role, email, dll.

4. **Config**
   - Konfigurasi aplikasi seperti nama aplikasi, nama perusahaan, dll.

## Keamanan

- Koneksi ke Google Sheets menggunakan Service Account dengan kredensial yang aman
- Hanya superadmin yang dapat mengakses fitur sinkronisasi dan restore
- Konfirmasi diperlukan sebelum melakukan restore data untuk mencegah kehilangan data

## Pemecahan Masalah

### Koneksi Gagal

Jika koneksi ke Google Sheets gagal:

1. Pastikan file `service_account_key.json` ada dan valid
2. Pastikan ID spreadsheet benar
3. Pastikan Service Account memiliki akses ke spreadsheet

### Data Tidak Tersinkronisasi

Jika data tidak tersinkronisasi secara otomatis:

1. Periksa status koneksi di tab "Google Sheets"
2. Coba sinkronisasi manual dengan tombol "Sinkronkan Sekarang"
3. Periksa log aplikasi untuk pesan error

### Restore Gagal

Jika restore data gagal:

1. Pastikan tab yang dipilih ada dan berisi data
2. Periksa format data di Google Sheets
3. Coba restore dari tab yang berbeda
