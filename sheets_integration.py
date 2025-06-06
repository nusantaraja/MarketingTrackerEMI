"""
Integration Module for AI Marketing Tracker with Google Sheets

This module integrates the Google Sheets sync functionality into the main application.
It provides UI components for manual sync and restore operations, including
confirmation and last sync time display for manual sync.
"""

import streamlit as st
import os
from datetime import datetime
from data_hooks import (
    manual_sync_all, 
    manual_restore_all,
    get_available_tabs
)
# Import helper to get last sync time
from google_sheets_sync import get_last_manual_sync_time 

def add_google_sheets_sync_ui():
    """Add Google Sheets sync UI components to the settings page."""
    st.subheader("Google Sheets Sync")
    
    st.info("""
    Data dari aplikasi ini secara otomatis disinkronkan ke Google Sheets setiap kali ada perubahan data.
    Sinkronisasi manual di bawah ini hanya menambahkan data baru yang belum ada di sheet (incremental).
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Sinkronisasi Manual (Incremental)**")
        st.write("Hanya menambahkan data baru dari aplikasi ke Google Sheets.")
        
        # Display last sync time
        last_sync_time = get_last_manual_sync_time()
        if last_sync_time:
            st.caption(f"Sinkronisasi manual terakhir berhasil: {last_sync_time} WIB")
        else:
            st.caption("Sinkronisasi manual belum pernah dilakukan.")
            
        # Confirmation before syncing
        sync_button_placeholder = st.empty()
        confirm_placeholder = st.empty()
        
        if sync_button_placeholder.button("Sinkronkan Data Baru Sekarang", use_container_width=True, key="manual_sync_start"):
            sync_button_placeholder.empty() # Hide the initial button
            with confirm_placeholder.container():
                st.warning("Anda yakin ingin menjalankan sinkronisasi manual? Ini hanya akan menambahkan data baru yang belum ada di Google Sheet.")
                col_confirm, col_cancel = st.columns(2)
                if col_confirm.button("Ya, Lanjutkan Sinkronisasi", use_container_width=True, key="manual_sync_confirm"):
                    confirm_placeholder.empty() # Clear confirmation
                    with st.spinner("Menyinkronkan data baru ke Google Sheets..."):
                        # Call sync with incremental=True
                        success, message = manual_sync_all(incremental=True) 
                        
                        if success:
                            st.success(message)
                            # Rerun to update last sync time display
                            st.rerun() 
                        else:
                            st.error(message)
                            # Restore button if sync fails
                            sync_button_placeholder.button("Sinkronkan Data Baru Sekarang", use_container_width=True, key="manual_sync_retry") 
                if col_cancel.button("Batal", use_container_width=True, key="manual_sync_cancel"):
                    confirm_placeholder.empty() # Clear confirmation
                    # Restore button
                    sync_button_placeholder.button("Sinkronkan Data Baru Sekarang", use_container_width=True, key="manual_sync_restart") 

    
    with col2:
        st.write("**Restore Data (Overwrite)**")
        st.write("**PERHATIAN:** Memulihkan data dari Google Sheets akan **MENIMPA** semua data lokal.")
        
        # Get available tabs
        success, message, tab_names = get_available_tabs()
        
        if success and tab_names:
            # Filter only the main data sheets for restore options
            restore_options = [name for name in tab_names if name in TABLE_MAP.values()]
            if restore_options:
                selected_tab = st.selectbox(
                    "Pilih sheet sumber untuk restore (akan menimpa data lokal)",
                    options=restore_options
                )
                
                # Confirmation for restore
                st.warning(f"Anda yakin ingin me-restore data dari sheet 	{selected_tab}	? Ini akan **MENGHAPUS** data lokal saat ini dan menggantinya.")
                if st.checkbox(f"Ya, saya mengerti dan ingin melanjutkan restore dari 	{selected_tab}	", key=f"confirm_restore_{selected_tab}"):
                    if st.button("Restore Data dari Sheet Terpilih", use_container_width=True, type="primary"):
                        with st.spinner(f"Memulihkan data dari sheet 	{selected_tab}	..."):
                            # Find the internal table name corresponding to the selected sheet
                            internal_table_name = None
                            for key, value in TABLE_MAP.items():
                                if value == selected_tab:
                                    internal_table_name = key
                                    break
                            
                            if internal_table_name:
                                # Call restore for the specific table
                                # Assuming data_hooks has a function like manual_restore_one(table_name)
                                # If not, need to adapt or call google_sheets_sync directly
                                try:
                                    from data_hooks import manual_restore_one
                                    success, message = manual_restore_one(internal_table_name)
                                except ImportError:
                                     # Fallback or error if specific restore hook isn't available
                                     st.error("Fungsi restore spesifik tidak ditemukan. Menggunakan restore semua (jika tersedia).")
                                     # Or call sync instance directly (less ideal)
                                     # from google_sheets_sync import get_sync_instance
                                     # sync = get_sync_instance()
                                     # success, message = sync.restore_data(internal_table_name)
                                     success, message = False, "Fungsi restore spesifik tidak ada."
                                     
                                if success:
                                    st.success(message + " Silakan refresh halaman.")
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error(f"Nama tabel internal tidak ditemukan untuk sheet 	{selected_tab}	.")
            else:
                 st.info("Tidak ada sheet data utama (Activities, Followups, Users, Config) yang ditemukan untuk di-restore.")

        elif not success:
            st.error(f"Tidak dapat mengambil daftar tab dari Google Sheets: {message}")
        else: # Success but no tabs
             st.info("Tidak ada sheet yang ditemukan di Google Sheet.")
    
    st.divider()
    
    # Information about automatic sync
    st.subheader("Informasi Sinkronisasi Otomatis")
    
    st.write("""
    **Sinkronisasi Otomatis:**
    
    Data secara otomatis disinkronkan ke Google Sheets setiap kali ada perubahan pada:
    - Aktivitas pemasaran (tambah, edit, hapus)
    - Follow-up (tambah)
    - Pengguna (tambah, hapus)
    - Konfigurasi aplikasi
    
    Sinkronisasi otomatis ini bersifat **incremental** (hanya mengirim data baru/yang berubah).
    
    **Catatan Penting:**
    
    Sinkronisasi manual di atas juga bersifat incremental dan berguna jika Anda merasa ada data yang belum tersinkronisasi.
    Restore data bersifat **overwrite** dan harus digunakan dengan hati-hati.
    """)
    
    # Display current connection status
    st.subheader("Status Koneksi")
    
    from google_sheets_sync import get_sync_instance
    
    try:
        sync = get_sync_instance()
        if sync.connect():
            st.success(f"Terhubung ke Google Sheets: {sync.spreadsheet.title}")
            # st.write(f"Tab bulan ini: {sync.get_current_month_tab_name()}") # Monthly tabs not implemented
        else:
            st.error("Tidak dapat terhubung ke Google Sheets.")
    except Exception as e:
        st.error(f"Error saat memeriksa koneksi: {e}")
