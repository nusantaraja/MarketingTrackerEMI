"""
Integration of Google Sheets sync with main application

This module updates the main application to include Google Sheets sync functionality.
"""

import os
import sys
import shutil
from app_with_edit_delete import *
from sheets_integration import add_google_sheets_sync_ui

# Override data functions with hooked versions
from data_hooks import (
    add_marketing_activity,
    edit_marketing_activity,
    delete_marketing_activity,
    add_followup,
    add_user,
    delete_user,
    update_app_config
)

# Update the show_settings_page function to include Google Sheets sync UI
def show_settings_page_with_sheets():
    st.title("Pengaturan")
    
    # Hanya superadmin yang bisa mengakses halaman ini
    if st.session_state.user['role'] != 'superadmin':
        st.error("Anda tidak memiliki akses ke halaman ini.")
        return
    
    # Tab untuk pengaturan umum, backup/restore, dan Google Sheets
    tab1, tab2, tab3 = st.tabs(["Pengaturan Umum", "Backup & Restore", "Google Sheets"])
    
    with tab1:
        st.subheader("Pengaturan Aplikasi")
        
        # Ambil konfigurasi saat ini
        config = get_app_config()
        
        # Form pengaturan
        with st.form("settings_form"):
            app_name = st.text_input("Nama Aplikasi", config.get('app_name', 'AI Suara Marketing Tracker'))
            company_name = st.text_input("Nama Perusahaan", config.get('company_name', 'AI Suara'))
            
            submitted = st.form_submit_button("Simpan Pengaturan", use_container_width=True)
            
            if submitted:
                # Update konfigurasi
                new_config = {
                    'app_name': app_name,
                    'company_name': company_name
                }
                
                success, message = update_app_config(new_config)
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    with tab2:
        st.subheader("Backup & Restore Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Backup Data**")
            st.write("Backup data aplikasi ke file.")
            
            if st.button("Backup Data Sekarang", use_container_width=True):
                success, message, backup_file = backup_data()
                
                if success:
                    st.success(message)
                    
                    # Download link
                    with open(backup_file, "rb") as file:
                        st.download_button(
                            label="Download Backup File",
                            data=file,
                            file_name=os.path.basename(backup_file),
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                else:
                    st.error(message)
        
        with col2:
            st.write("**Restore Data**")
            st.write("Restore data aplikasi dari file backup.")
            
            uploaded_file = st.file_uploader("Pilih file backup", type=["zip"])
            
            if uploaded_file is not None:
                if st.button("Restore Data", use_container_width=True):
                    # Simpan file yang diupload
                    with open("temp_backup.zip", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Restore data
                    success, message = restore_data("temp_backup.zip")
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        st.divider()
        
        st.subheader("Validasi & Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Validasi Integritas Data**")
            st.write("Periksa integritas data aplikasi.")
            
            if st.button("Validasi Data", use_container_width=True):
                success, message, issues = validate_data_integrity()
                
                if success and not issues:
                    st.success(message)
                elif success and issues:
                    st.warning(message)
                    st.write("Masalah yang ditemukan:")
                    for issue in issues:
                        st.write(f"- {issue}")
                else:
                    st.error(message)
        
        with col2:
            st.write("**Export Data ke CSV**")
            st.write("Export data aplikasi ke file CSV.")
            
            export_type = st.selectbox(
                "Pilih data yang akan diexport",
                ["Aktivitas Pemasaran", "Follow-up", "Pengguna"]
            )
            
            if st.button("Export Data", use_container_width=True):
                if export_type == "Aktivitas Pemasaran":
                    success, message, export_file = export_to_csv("activities")
                elif export_type == "Follow-up":
                    success, message, export_file = export_to_csv("followups")
                else:
                    success, message, export_file = export_to_csv("users")
                
                if success:
                    st.success(message)
                    
                    # Download link
                    with open(export_file, "rb") as file:
                        st.download_button(
                            label="Download CSV File",
                            data=file,
                            file_name=os.path.basename(export_file),
                            mime="text/csv",
                            use_container_width=True
                        )
                else:
                    st.error(message)
    
    with tab3:
        # Add Google Sheets sync UI
        add_google_sheets_sync_ui()

# Override the original show_settings_page function
def main_with_sheets():
    # Inisialisasi session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Cek login
    if not st.session_state.logged_in:
        user = authenticate_user()
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
        else:
            show_login_page()
            return
    
    # Tampilkan sidebar dan dapatkan menu yang dipilih
    menu = show_sidebar()
    
    # Tampilkan halaman sesuai menu yang dipilih
    if menu == "Dashboard":
        if st.session_state.user['role'] == 'superadmin':
            show_superadmin_dashboard()
        else:
            show_marketing_dashboard()
    elif menu == "Aktivitas Pemasaran":
        show_marketing_activities_page()
    elif menu == "Follow-up":
        show_followup_page()
    elif menu == "Manajemen Pengguna":
        show_user_management_page()
    elif menu == "Pengaturan":
        show_settings_page_with_sheets()  # Use the updated settings page
    elif menu == "Profil":
        show_profile_page()

# Replace the main function
if __name__ == "__main__":
    main_with_sheets()
