"""
Integration Module for AI Marketing Tracker with Google Sheets

This module integrates the Google Sheets sync functionality into the main application.
It provides UI components for manual sync and restore operations.
"""

import streamlit as st
import os
from datetime import datetime
from data_hooks import (
    manual_sync_all, 
    manual_restore_all,
    get_available_tabs
)

def add_google_sheets_sync_ui():
    """Add Google Sheets sync UI components to the settings page."""
    st.subheader("Google Sheets Sync")
    
    st.info("""
    Data dari aplikasi ini secara otomatis disinkronkan ke Google Sheets setiap kali ada perubahan data.
    Setiap bulan, tab baru akan dibuat di Google Sheets untuk menyimpan data bulan tersebut.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Sinkronisasi Manual**")
        st.write("Sinkronkan semua data ke Google Sheets secara manual.")
        
        if st.button("Sinkronkan Sekarang", use_container_width=True):
            with st.spinner("Menyinkronkan data ke Google Sheets..."):
                success, message = manual_sync_all()
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    with col2:
        st.write("**Restore Data**")
        st.write("Pulihkan data dari Google Sheets.")
        
        # Get available tabs
        success, message, tab_names = get_available_tabs()
        
        if success and tab_names:
            selected_tab = st.selectbox(
                "Pilih tab untuk restore data",
                options=tab_names
            )
            
            if st.button("Restore Data", use_container_width=True):
                # Confirmation
                confirm = st.checkbox("Saya mengerti bahwa ini akan menimpa data lokal dengan data dari Google Sheets")
                
                if confirm:
                    with st.spinner("Memulihkan data dari Google Sheets..."):
                        success, message = manual_restore_all(selected_tab)
                        
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
        else:
            st.error("Tidak dapat mengambil daftar tab dari Google Sheets.")
    
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
    
    **Rotasi Tab Bulanan:**
    
    Setiap bulan, tab baru akan dibuat di Google Sheets dengan format nama `YYYY_MM`.
    Data akan disimpan di tab sesuai dengan bulan saat ini.
    
    **Catatan Penting:**
    
    Sinkronisasi terjadwal secara periodik saat ini tidak tersedia. 
    Untuk memastikan data selalu tersinkronisasi, gunakan tombol "Sinkronkan Sekarang" secara manual.
    """)
    
    # Display current connection status
    st.subheader("Status Koneksi")
    
    from google_sheets_sync import get_sync_instance
    
    try:
        sync = get_sync_instance()
        if sync.connect():
            st.success(f"Terhubung ke Google Sheets: {sync.spreadsheet.title}")
            st.write(f"Tab bulan ini: {sync.get_current_month_tab_name()}")
        else:
            st.error("Tidak dapat terhubung ke Google Sheets.")
    except Exception as e:
        st.error(f"Error saat memeriksa koneksi: {e}")
