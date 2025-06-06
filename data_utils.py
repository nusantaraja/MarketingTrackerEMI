import os
import yaml
import shutil
import datetime
import pandas as pd # Import pandas here

# Fungsi untuk membuat backup data
def backup_data():
    """
    Membuat backup dari seluruh file database YAML.
    Returns:
        tuple: (bool, str, str or None) -> (success, message, backup_file_path or None)
    """
    # Direktori data dan backup
    data_dir = os.path.join(os.getcwd(), "data")
    backup_dir = os.path.join(os.getcwd(), "backup")
    
    try:
        # Buat direktori backup jika belum ada
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Timestamp untuk nama folder backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = os.path.join(backup_dir, f"backup_{timestamp}")
        os.makedirs(backup_folder)
        
        # Salin semua file YAML ke folder backup
        copied_files = 0
        for filename in os.listdir(data_dir):
            if filename.endswith(".yaml"):
                src_file = os.path.join(data_dir, filename)
                dst_file = os.path.join(backup_folder, filename)
                shutil.copy2(src_file, dst_file)
                copied_files += 1
        
        if copied_files > 0:
            # Zip the backup folder
            backup_zip_path = shutil.make_archive(backup_folder, 'zip', backup_folder)
            # Remove the original folder after zipping
            shutil.rmtree(backup_folder)
            return True, f"Backup berhasil dibuat: {os.path.basename(backup_zip_path)}", backup_zip_path
        else:
            # Remove empty backup folder
            os.rmdir(backup_folder)
            return False, "Tidak ada file data yang ditemukan untuk dibackup.", None
            
    except Exception as e:
        return False, f"Gagal membuat backup: {str(e)}", None

# Fungsi untuk memulihkan data dari backup
def restore_data(backup_zip_file):
    """
    Memulihkan data dari file backup zip yang ditentukan.
    Returns:
        tuple: (bool, str) -> (success, message)
    """
    # Direktori data dan temporary extraction folder
    data_dir = os.path.join(os.getcwd(), "data")
    temp_extract_dir = os.path.join(os.getcwd(), "temp_restore_extract")
    
    # Pastikan file backup zip ada
    if not os.path.exists(backup_zip_file):
        return False, f"File backup {backup_zip_file} tidak ditemukan"
    
    try:
        # Hapus temporary directory jika ada sebelumnya
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
            
        # Ekstrak file zip ke temporary directory
        shutil.unpack_archive(backup_zip_file, temp_extract_dir, 'zip')
        
        # Pastikan direktori data ada
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Salin semua file YAML dari folder hasil ekstrak ke direktori data
        restored_files = 0
        for filename in os.listdir(temp_extract_dir):
            if filename.endswith(".yaml"):
                src_file = os.path.join(temp_extract_dir, filename)
                dst_file = os.path.join(data_dir, filename)
                shutil.copy2(src_file, dst_file)
                restored_files += 1
                
        # Hapus temporary directory
        shutil.rmtree(temp_extract_dir)
        
        if restored_files > 0:
            return True, "Data berhasil dipulihkan"
        else:
            return False, "Tidak ada file data yang ditemukan dalam backup."
            
    except Exception as e:
        # Hapus temporary directory jika terjadi error
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        return False, f"Gagal memulihkan data: {str(e)}"

# Fungsi untuk ekspor data ke CSV
def export_to_csv(data_type):
    """
    Mengekspor data (activities, followups, users) ke file CSV.
    Returns:
        tuple: (bool, str, str or None) -> (success, message, csv_file_path or None)
    """
    data_dir = os.path.join(os.getcwd(), "data")
    exports_dir = os.path.join(os.getcwd(), "exports")
    
    # Tentukan file YAML sumber berdasarkan data_type
    if data_type == "activities":
        yaml_file = os.path.join(data_dir, "marketing_activities.yaml")
        data_key = "marketing_activities"
        csv_filename = f"export_activities_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    elif data_type == "followups":
        yaml_file = os.path.join(data_dir, "followups.yaml")
        data_key = "followups"
        csv_filename = f"export_followups_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    elif data_type == "users":
        yaml_file = os.path.join(data_dir, "users.yaml")
        data_key = "users"
        csv_filename = f"export_users_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    else:
        return False, "Tipe data export tidak valid.", None

    try:
        # Baca data dari YAML
        if not os.path.exists(yaml_file):
            return False, f"File data {os.path.basename(yaml_file)} tidak ditemukan.", None
            
        with open(yaml_file, 'r', encoding='utf-8') as file:
            yaml_data = yaml.safe_load(file)
            
        if not yaml_data or data_key not in yaml_data or not yaml_data[data_key]:
            return False, f"Tidak ada data {data_type} untuk diexport.", None
            
        data_list = yaml_data[data_key]
        
        # Konversi data ke DataFrame
        df = pd.DataFrame(data_list)
        
        # Buat direktori exports jika belum ada
        if not os.path.exists(exports_dir):
            os.makedirs(exports_dir)
            
        csv_file_path = os.path.join(exports_dir, csv_filename)
        
        # Simpan ke file CSV
        df.to_csv(csv_file_path, index=False, encoding='utf-8')
        
        return True, f"Data {data_type} berhasil diexport ke {csv_filename}", csv_file_path
        
    except Exception as e:
        return False, f"Gagal mengekspor data {data_type}: {str(e)}", None

# Fungsi untuk validasi integritas data
def validate_data_integrity():
    """
    Memvalidasi integritas data di seluruh file YAML.
    Returns:
        tuple: (bool, str, list) -> (success, message, list_of_issues)
    """
    data_dir = os.path.join(os.getcwd(), "data")
    required_files = ["users.yaml", "marketing_activities.yaml", "followups.yaml", "config.yaml"]
    issues = []

    # 1. Periksa keberadaan file
    for filename in required_files:
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            issues.append(f"File tidak ditemukan: {filename}")
    
    if issues:
        return False, "Validasi gagal: File data penting hilang.", issues

    # 2. Periksa struktur data dasar
    try:
        # Users
        users_file = os.path.join(data_dir, "users.yaml")
        with open(users_file, 'r', encoding='utf-8') as file:
            users_data = yaml.safe_load(file)
        if not isinstance(users_data, dict) or "users" not in users_data or not isinstance(users_data["users"], list):
            issues.append("Struktur data users.yaml tidak valid (harus dict dengan key 'users' berisi list).")
        
        # Activities
        activities_file = os.path.join(data_dir, "marketing_activities.yaml")
        with open(activities_file, 'r', encoding='utf-8') as file:
            activities_data = yaml.safe_load(file)
        if not isinstance(activities_data, dict) or "marketing_activities" not in activities_data or not isinstance(activities_data["marketing_activities"], list):
            issues.append("Struktur data marketing_activities.yaml tidak valid (harus dict dengan key 'marketing_activities' berisi list).")
        
        # Followups
        followups_file = os.path.join(data_dir, "followups.yaml")
        with open(followups_file, 'r', encoding='utf-8') as file:
            followups_data = yaml.safe_load(file)
        if not isinstance(followups_data, dict) or "followups" not in followups_data or not isinstance(followups_data["followups"], list):
            issues.append("Struktur data followups.yaml tidak valid (harus dict dengan key 'followups' berisi list).")
        
        # Config
        config_file = os.path.join(data_dir, "config.yaml")
        with open(config_file, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        if not isinstance(config_data, dict):
            issues.append("Struktur data config.yaml tidak valid (harus dict).")
        # Add more specific config checks if needed, e.g., presence of certain keys
        # required_config_keys = ["app_name", "company_name"]
        # for key in required_config_keys:
        #     if key not in config_data:
        #         issues.append(f"Kunci konfigurasi wajib '{key}' tidak ditemukan di config.yaml")

        if issues:
            return False, "Validasi gagal: Struktur data tidak valid.", issues
        else:
            return True, "Integritas data valid.", []
            
    except Exception as e:
        error_message = f"Error saat memvalidasi struktur data: {str(e)}"
        return False, error_message, [error_message]

# Fungsi untuk sinkronisasi dengan GitHub (Placeholder - Implementasi sebenarnya di luar scope data_utils)
def prepare_for_github_sync():
    """
    Menyiapkan file-file untuk sinkronisasi dengan GitHub (contoh: .gitignore, README).
    Returns:
        tuple: (bool, str) -> (success, message)
    """
    try:
        # Buat file .gitignore
        gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Virtual environments
venv/
env/
ENV/

# Local development settings
.env

# Backup files
backup/
*.zip

# Streamlit specific
.streamlit/secrets.toml

# Exports
exports/
*.csv

# Temporary files
temp_restore_extract/
"""
        gitignore_file = os.path.join(os.getcwd(), ".gitignore")
        with open(gitignore_file, 'w', encoding='utf-8') as file:
            file.write(gitignore_content)
        
        # Buat README.md (jika belum ada atau perlu update)
        readme_file = os.path.join(os.getcwd(), "README.md")
        if not os.path.exists(readme_file):
            readme_content = """# AI Suara Marketing Tracker

Aplikasi Streamlit untuk mencatat dan memonitor aktivitas pemasaran.

(Tambahkan deskripsi lebih lanjut di sini)
"""
            with open(readme_file, 'w', encoding='utf-8') as file:
                file.write(readme_content)
        
        return True, "File dasar (.gitignore, README.md) untuk sinkronisasi GitHub berhasil disiapkan/diperbarui."
    except Exception as e:
        return False, f"Gagal menyiapkan file untuk GitHub: {str(e)}"

