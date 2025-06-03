import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta
import os
from utils_with_edit_delete import (
    initialize_database, check_login, login, logout,
    get_all_users, add_user, delete_user, get_all_marketing_activities,
    get_marketing_activities_by_username, add_marketing_activity,
    edit_marketing_activity, delete_marketing_activity,
    get_activity_by_id, get_all_followups, get_followups_by_activity_id,
    get_followups_by_username, add_followup, update_activity_status,
    get_app_config, update_app_config
)
from data_utils import backup_data, restore_data, validate_data_integrity, export_to_csv


# Initialize database
initialize_database()

# Page configuration
st.set_page_config(
    page_title="AI Suara Marketing Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Status mapping for consistent display and reverse mapping for saving
STATUS_MAPPING = {
    'baru': 'Baru',
    'dalam_proses': 'Dalam Proses',
    'berhasil': 'Berhasil',
    'gagal': 'Gagal'
}
REVERSE_STATUS_MAPPING = {v: k for k, v in STATUS_MAPPING.items()}

def add_marketing_activity_wrapper(
    marketer_username, 
    prospect_name, 
    prospect_location,
    contact_person, 
    contact_position, 
    contact_phone,
    contact_email, 
    activity_date, 
    activity_type, 
    description,
    status # Add status parameter
):
    """Wrapper function for adding marketing activity with backup"""
    try:
        success, message, activity_id = add_marketing_activity(
            marketer_username,
            prospect_name,
            prospect_location,
            contact_person,
            contact_position,
            contact_phone,
            contact_email,
            activity_date,
            activity_type,
            description,
            status # Pass status to the backend function
        )
        if success:
            # Trigger backup (assuming backup_data is defined elsewhere correctly)
            # backup_success, backup_msg, _ = backup_data() 
            # if not backup_success:
            #     st.warning(f"Aktivitas berhasil ditambahkan, tetapi backup gagal: {backup_msg}")
            # else:
            #     st.success("Aktivitas berhasil ditambahkan dan dibackup.")
            st.success(message) # Keep original success message for now
            return True, message, activity_id
        else:
            st.error(message)
            return False, message, None
            
    except Exception as e:
        st.error(f"Error saat menambahkan aktivitas: {str(e)}")
        return False, str(e), None

def show_login_page():
    """Display the login page"""
    # Custom CSS for login page
    st.markdown("""
        <style>
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
            }
            .css-1544g2n {
                padding-top: 0 !important;
            }
            .css-18e3th9 {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }
            .css-1d391kg {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }
            div[data-testid="stVerticalBlock"] {
                gap: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Logo and title
    st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; margin-top: 20px; margin-bottom: 20px;">
            <img src="static/img/logo.jpg" style="max-width: 180px; margin: 0 auto;">
        </div>
        <h1 style="text-align: center; margin-bottom: 30px;">AI Suara Marketing Tracker</h1>
    """, unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if login(username, password):
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
        
        # Footer
        st.markdown("""
            <div style="text-align: center; margin-top: 20px; font-size: 0.8rem; color: #6c757d;">
                © 2025 AI Suara Marketing Tracker
            </div>
        """, unsafe_allow_html=True)

def show_sidebar():
    """Display the application sidebar"""
    with st.sidebar:
        st.title("AI Suara Marketing")
        
        user = st.session_state.user
        st.write(f"Selamat datang, **{user['name']}**!")
        st.write(f"Role: **{user['role'].capitalize()}**")
        
        st.divider()
        
        # Menu based on user role
        if user['role'] == 'superadmin':
            menu = st.radio(
                "Menu",
                ["Dashboard", "Aktivitas Pemasaran", "Follow-up", "Manajemen Pengguna", "Pengaturan"]
            )
        else:
            menu = st.radio(
                "Menu",
                ["Dashboard", "Aktivitas Pemasaran", "Follow-up", "Profil"]
            )
        
        st.divider()
        
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    
    return menu

def show_superadmin_dashboard():
    """Display superadmin dashboard with analytics"""
    st.title("Dashboard Superadmin")
    
    # Get all data
    activities = get_all_marketing_activities()
    followups = get_all_followups()
    users = get_all_users()
    marketing_users = [user for user in users if user['role'] == 'marketing']
    
    if not activities:
        st.info("Belum ada data aktivitas pemasaran. Tambahkan aktivitas pemasaran terlebih dahulu.")
        return
    
    activities_df = pd.DataFrame(activities)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Aktivitas", len(activities))
    with col2:
        st.metric("Total Prospek", activities_df['prospect_name'].nunique())
    with col3:
        st.metric("Total Marketing", len(marketing_users))
    with col4:
        st.metric("Total Follow-up", len(followups) if followups else 0)
    
    # First row of charts
    st.subheader("Analisis Aktivitas Pemasaran")
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution
        status_counts = activities_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Jumlah']
        status_counts['Status'] = status_counts['Status'].map(lambda x: STATUS_MAPPING.get(x, x))
        
        fig = px.pie(
            status_counts, 
            values='Jumlah', 
            names='Status',
            title='Distribusi Status Prospek',
            color='Status',
            color_discrete_map={
                'Baru': '#3498db',
                'Dalam Proses': '#f39c12',
                'Berhasil': '#2ecc71',
                'Gagal': '#e74c3c'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Activities per marketer
        marketer_counts = activities_df['marketer_username'].value_counts().reset_index()
        marketer_counts.columns = ['Marketing', 'Jumlah Aktivitas']
        
        fig = px.bar(
            marketer_counts,
            x='Marketing',
            y='Jumlah Aktivitas',
            title='Jumlah Aktivitas per Marketing',
            color='Jumlah Aktivitas',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Second row of charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Activities by location
        location_counts = activities_df['prospect_location'].value_counts().reset_index()
        location_counts.columns = ['Lokasi', 'Jumlah']
        
        fig = px.bar(
            location_counts.head(10),
            x='Lokasi',
            y='Jumlah',
            title='10 Lokasi Prospek Teratas',
            color='Jumlah',
            color_continuous_scale=px.colors.sequential.Plasma
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Activities by type
        if 'activity_type' in activities_df.columns:
            type_counts = activities_df['activity_type'].value_counts().reset_index()
            type_counts.columns = ['Jenis Aktivitas', 'Jumlah']
            
            fig = px.pie(
                type_counts,
                values='Jumlah',
                names='Jenis Aktivitas',
                title='Distribusi Jenis Aktivitas',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent activities
    st.subheader("Aktivitas Pemasaran Terbaru")
    activities_df['created_at'] = pd.to_datetime(activities_df['created_at'])
    activities_df = activities_df.sort_values('created_at', ascending=False)
    
    display_columns = ['marketer_username', 'prospect_name', 'prospect_location', 
                      'activity_type', 'status', 'created_at']
    
    column_mapping = {
        'marketer_username': 'Marketing',
        'prospect_name': 'Nama Prospek',
        'prospect_location': 'Lokasi',
        'activity_type': 'Jenis Aktivitas',
        'status': 'Status',
        'created_at': 'Tanggal Dibuat'
    }
    
    display_df = activities_df[display_columns].rename(columns=column_mapping)
    display_df['Status'] = display_df['Status'].map(lambda x: STATUS_MAPPING.get(x, x))
    st.dataframe(display_df.head(10), use_container_width=True)
    
    # Upcoming follow-ups
    if followups:
        st.subheader("Follow-up yang Akan Datang")
        followups_df = pd.DataFrame(followups)
        followups_df['next_followup_date'] = pd.to_datetime(followups_df['next_followup_date'])
        
        today = datetime.now()
        next_week = today + timedelta(days=7)
        upcoming_followups = followups_df[
            (followups_df['next_followup_date'] >= today) & 
            (followups_df['next_followup_date'] <= next_week)
        ]
        
        if not upcoming_followups.empty:
            upcoming_followups = upcoming_followups.merge(
                activities_df[['id', 'prospect_name']],
                left_on='activity_id',
                right_on='id',
                how='left'
            )
            
            display_columns = ['marketer_username', 'prospect_name', 'next_followup_date', 'next_action']
            column_mapping = {
                'marketer_username': 'Marketing',
                'prospect_name': 'Nama Prospek',
                'next_followup_date': 'Tanggal Follow-up',
                'next_action': 'Tindakan Selanjutnya'
            }
            
            display_df = upcoming_followups[display_columns].rename(columns=column_mapping)
            display_df = display_df.sort_values('Tanggal Follow-up')
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Tidak ada follow-up yang dijadwalkan dalam 7 hari ke depan.")

def show_marketing_dashboard():
    st.title("DASHBOARD MARKETING")
    
    user = st.session_state.user
    username = user['username']
    
    # Ambil data aktivitas marketing
    activities = get_marketing_activities_by_username(username)
    followups = get_followups_by_username(username)
    
    # Jika tidak ada data, tampilkan pesan
    if not activities:
        st.info("Anda belum memiliki aktivitas pemasaran. Tambahkan aktivitas pemasaran terlebih dahulu.")
        return
    
    # Konversi ke DataFrame untuk analisis
    activities_df = pd.DataFrame(activities)
    
    # Metrik utama
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Aktivitas", len(activities))
    with col2:
        st.metric("Total Prospek", activities_df['prospect_name'].nunique())
    with col3:
        if followups:
            st.metric("Total Follow-up", len(followups))
        else:
            st.metric("Total Follow-up", 0)
    
    # Baris pertama grafik
    st.subheader("Analisis Aktivitas Pemasaran")
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribusi status prospek
        status_counts = activities_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Jumlah']
        
        # Mapping status untuk tampilan yang lebih baik
        status_counts['Status'] = status_counts['Status'].map(lambda x: STATUS_MAPPING.get(x, x))
        
        fig = px.pie(
            status_counts, 
            values='Jumlah', 
            names='Status',
            title='Distribusi Status Prospek',
            color='Status',
            color_discrete_map={
                'Baru': '#3498db',
                'Dalam Proses': '#f39c12',
                'Berhasil': '#2ecc71',
                'Gagal': '#e74c3c'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Aktivitas per jenis
        if 'activity_type' in activities_df.columns:
            type_counts = activities_df['activity_type'].value_counts().reset_index()
            type_counts.columns = ['Jenis Aktivitas', 'Jumlah']
            
            fig = px.pie(
                type_counts,
                values='Jumlah',
                names='Jenis Aktivitas',
                title='Distribusi Jenis Aktivitas',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Baris kedua grafik
    col1, col2 = st.columns(2)
    
    with col1:
        # Aktivitas per lokasi
        location_counts = activities_df['prospect_location'].value_counts().reset_index()
        location_counts.columns = ['Lokasi', 'Jumlah']
        
        fig = px.bar(
            location_counts.head(10),
            x='Lokasi',
            y='Jumlah',
            title='10 Lokasi Prospek Teratas',
            color='Jumlah',
            color_continuous_scale=px.colors.sequential.Plasma
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Daftar aktivitas terbaru
    st.subheader("Aktivitas Pemasaran Terbaru")
    
    # Konversi created_at ke datetime dan urutkan
    activities_df['created_at'] = pd.to_datetime(activities_df['created_at'])
    activities_df = activities_df.sort_values('created_at', ascending=False)
    
    # Pilih kolom yang ingin ditampilkan
    display_columns = ['prospect_name', 'prospect_location', 
                      'activity_type', 'status', 'created_at']
    
    # Rename kolom untuk tampilan yang lebih baik
    column_mapping = {
        'prospect_name': 'Nama Prospek',
        'prospect_location': 'Lokasi',
        'activity_type': 'Jenis Aktivitas',
        'status': 'Status',
        'created_at': 'Tanggal Dibuat'
    }
    
    display_df = activities_df[display_columns].rename(columns=column_mapping)
    
    # Mapping status untuk tampilan yang lebih baik
    display_df['Status'] = display_df['Status'].map(lambda x: STATUS_MAPPING.get(x, x))
    
    # Tampilkan 10 aktivitas terbaru
    st.dataframe(display_df.head(10), use_container_width=True)
    
    # Daftar follow-up yang akan datang
    if followups:
        st.subheader("Follow-up yang Akan Datang")
        
        followups_df = pd.DataFrame(followups)
        followups_df['next_followup_date'] = pd.to_datetime(followups_df['next_followup_date'])
        
        # Filter follow-up yang akan datang (dalam 7 hari ke depan)
        today = datetime.now()
        next_week = today + timedelta(days=7)
        upcoming_followups = followups_df[
            (followups_df['next_followup_date'] >= today) & 
            (followups_df['next_followup_date'] <= next_week)
        ]
        
        if not upcoming_followups.empty:
            # Gabungkan dengan data aktivitas untuk mendapatkan nama prospek
            upcoming_followups = upcoming_followups.merge(
                activities_df[['id', 'prospect_name']],
                left_on='activity_id',
                right_on='id',
                how='left'
            )
            
            # Pilih kolom yang ingin ditampilkan
            display_columns = ['prospect_name', 'next_followup_date', 'next_action']
            
            # Rename kolom untuk tampilan yang lebih baik
            column_mapping = {
                'prospect_name': 'Nama Prospek',
                'next_followup_date': 'Tanggal Follow-up',
                'next_action': 'Tindakan Selanjutnya'
            }
            
            display_df = upcoming_followups[display_columns].rename(columns=column_mapping)
            display_df = display_df.sort_values('Tanggal Follow-up')
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Tidak ada follow-up yang dijadwalkan dalam 7 hari ke depan.")

def show_marketing_activities_page():
    st.title("Aktivitas Pemasaran")
    
    user = st.session_state.user
    username = user['username']
    role = user['role']
    
    # Define tabs based on role
    if role == 'superadmin':
        tab_names = ["Lihat Aktivitas", "Tambah Aktivitas", "Edit Aktivitas", "Hapus Aktivitas"]
        tabs = st.tabs(tab_names)
        tab1, tab2, tab3, tab4 = tabs
    else: # marketing role
        tab_names = ["Lihat Aktivitas", "Tambah Aktivitas", "Edit Aktivitas"]
        tabs = st.tabs(tab_names)
        tab1, tab2, tab3 = tabs
        tab4 = None # Assign None to tab4 for marketing role
    
    # Ambil data aktivitas
    if role == 'superadmin':
        activities = get_all_marketing_activities()
    else:
        activities = get_marketing_activities_by_username(username)
    
    if not activities:
        st.info("Belum ada data aktivitas pemasaran.")
        activities_df = pd.DataFrame()
    else:
        activities_df = pd.DataFrame(activities)
        # Convert dates for proper display and sorting
        activities_df['activity_date'] = pd.to_datetime(activities_df['activity_date'])
        activities_df['created_at'] = pd.to_datetime(activities_df['created_at'])
        activities_df['updated_at'] = pd.to_datetime(activities_df['updated_at'])
        activities_df = activities_df.sort_values('created_at', ascending=False)

    with tab1:
        st.subheader("Daftar Aktivitas Pemasaran")
        
        if not activities_df.empty:
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.multiselect(
                    "Filter berdasarkan Status",
                    options=list(STATUS_MAPPING.values()),
                    default=list(STATUS_MAPPING.values())
                )
            with col2:
                filter_start_date = st.date_input("Filter Tanggal Mulai", value=None)
            with col3:
                filter_end_date = st.date_input("Filter Tanggal Akhir", value=None)
            
            # Apply filters
            filtered_df = activities_df.copy()
            
            # Map selected display status back to internal keys for filtering
            filter_status_keys = [REVERSE_STATUS_MAPPING[s] for s in filter_status]
            filtered_df = filtered_df[filtered_df['status'].isin(filter_status_keys)]
            
            if filter_start_date:
                filtered_df = filtered_df[filtered_df['activity_date'].dt.date >= filter_start_date]
            if filter_end_date:
                filtered_df = filtered_df[filtered_df['activity_date'].dt.date <= filter_end_date]
            
            # Prepare display dataframe
            display_columns = [
                'marketer_username', 'prospect_name', 'prospect_location', 
                'contact_person', 'contact_phone', 'activity_date', 
                'activity_type', 'status', 'updated_at'
            ]
            column_mapping = {
                'marketer_username': 'Marketing',
                'prospect_name': 'Nama Prospek',
                'prospect_location': 'Lokasi',
                'contact_person': 'Kontak Person',
                'contact_phone': 'Telepon',
                'activity_date': 'Tanggal Aktivitas',
                'activity_type': 'Jenis Aktivitas',
                'status': 'Status',
                'updated_at': 'Terakhir Update'
            }
            
            display_df = filtered_df[display_columns].rename(columns=column_mapping)
            display_df['Status'] = display_df['Status'].map(lambda x: STATUS_MAPPING.get(x, x))
            # Format dates for display
            display_df['Tanggal Aktivitas'] = display_df['Tanggal Aktivitas'].dt.strftime('%Y-%m-%d')
            display_df['Terakhir Update'] = display_df['Terakhir Update'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Tidak ada data aktivitas untuk ditampilkan.")

    with tab2:
        st.subheader("Tambah Aktivitas Pemasaran Baru")
        with st.form("add_activity_form"):
            prospect_name = st.text_input("Nama Prospek")
            prospect_location = st.text_input("Lokasi Prospek")
            contact_person = st.text_input("Nama Kontak Person")
            contact_position = st.text_input("Jabatan Kontak Person")
            contact_phone = st.text_input("Nomor Telepon Kontak")
            contact_email = st.text_input("Email Kontak")
            activity_date = st.date_input("Tanggal Aktivitas", value=datetime.now())
            activity_type = st.selectbox("Jenis Aktivitas", ["Telepon", "Email", "Meeting", "Presentasi", "Lainnya"])
            description = st.text_area("Deskripsi Aktivitas")
            # Add Status selection
            status_display = st.selectbox("Status", options=list(STATUS_MAPPING.values()), index=0) # Default to 'Baru'
            
            submitted = st.form_submit_button("Tambah Aktivitas", use_container_width=True)
            
            if submitted:
                if not all([prospect_name, prospect_location, contact_person, contact_phone, activity_date, activity_type, description, status_display]):
                    st.error("Semua field wajib diisi!")
                else:
                    # Map display status back to internal key
                    status_key = REVERSE_STATUS_MAPPING[status_display]
                    success, message, _ = add_marketing_activity_wrapper(
                        username, prospect_name, prospect_location, 
                        contact_person, contact_position, contact_phone, 
                        contact_email, activity_date, activity_type, description,
                        status_key # Pass the selected status key
                    )
                    if success:
                        st.success(message)
                        # Clear form or rerun? Rerun might be better to refresh tab1
                        st.rerun()
                    else:
                        st.error(message)

    with tab3:
        st.subheader("Edit Aktivitas Pemasaran")
        if not activities_df.empty:
            activity_options = {f"{row['prospect_name']} ({row['activity_date'].strftime('%Y-%m-%d')}) - ID: {row['id']}": row['id'] 
                              for index, row in activities_df.iterrows()}
            selected_activity_display = st.selectbox("Pilih Aktivitas untuk Diedit", options=list(activity_options.keys()))
            
            if selected_activity_display:
                selected_activity_id = activity_options[selected_activity_display]
                activity_to_edit = activities_df[activities_df['id'] == selected_activity_id].iloc[0]
                
                with st.form("edit_activity_form"):
                    st.write(f"Mengedit Aktivitas ID: {selected_activity_id}")
                    prospect_name = st.text_input("Nama Prospek", value=activity_to_edit['prospect_name'])
                    prospect_location = st.text_input("Lokasi Prospek", value=activity_to_edit['prospect_location'])
                    contact_person = st.text_input("Nama Kontak Person", value=activity_to_edit['contact_person'])
                    contact_position = st.text_input("Jabatan Kontak Person", value=activity_to_edit['contact_position'])
                    contact_phone = st.text_input("Nomor Telepon Kontak", value=activity_to_edit['contact_phone'])
                    contact_email = st.text_input("Email Kontak", value=activity_to_edit['contact_email'])
                    activity_date = st.date_input("Tanggal Aktivitas", value=activity_to_edit['activity_date'].date())
                    activity_type_options = ["Telepon", "Email", "Meeting", "Presentasi", "Lainnya"]
                    activity_type_index = activity_type_options.index(activity_to_edit['activity_type']) if activity_to_edit['activity_type'] in activity_type_options else 0
                    activity_type = st.selectbox("Jenis Aktivitas", options=activity_type_options, index=activity_type_index)
                    description = st.text_area("Deskripsi Aktivitas", value=activity_to_edit['description'])
                    
                    # Status selection for editing
                    status_options = list(STATUS_MAPPING.values())
                    current_status_display = STATUS_MAPPING.get(activity_to_edit['status'], 'Baru')
                    status_index = status_options.index(current_status_display) if current_status_display in status_options else 0
                    status_display = st.selectbox("Status", options=status_options, index=status_index)
                    
                    submitted = st.form_submit_button("Simpan Perubahan", use_container_width=True)
                    
                    if submitted:
                        if not all([prospect_name, prospect_location, contact_person, contact_phone, activity_date, activity_type, description, status_display]):
                            st.error("Semua field wajib diisi!")
                        else:
                            # Map display status back to internal key
                            status_key = REVERSE_STATUS_MAPPING[status_display]
                            success, message = edit_marketing_activity(
                                selected_activity_id, prospect_name, prospect_location, 
                                contact_person, contact_position, contact_phone, 
                                contact_email, activity_date, activity_type, description,
                                status_key # Pass the selected status key
                            )
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        else:
            st.info("Tidak ada aktivitas untuk diedit.")

    # Only render tab4 content if it exists (i.e., user is superadmin)
    if tab4:
        with tab4:
            st.subheader("Hapus Aktivitas Pemasaran")
            if not activities_df.empty:
                activity_options = {f"{row['prospect_name']} ({row['activity_date'].strftime('%Y-%m-%d')}) - ID: {row['id']}": row['id'] 
                                  for index, row in activities_df.iterrows()}
                selected_activity_display = st.selectbox("Pilih Aktivitas untuk Dihapus", options=list(activity_options.keys()), key="delete_activity_select") # Added key
                
                if selected_activity_display:
                    selected_activity_id = activity_options[selected_activity_display]
                    st.warning(f"Anda yakin ingin menghapus aktivitas untuk **{selected_activity_display.split(' (')[0]}** (ID: {selected_activity_id})? Tindakan ini tidak dapat dibatalkan dan akan menghapus semua follow-up terkait.")
                    
                    if st.button("Hapus Aktivitas Ini", type="primary", use_container_width=True, key="delete_activity_button"): # Added key
                        success, message = delete_marketing_activity(selected_activity_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.info("Tidak ada aktivitas untuk dihapus.")

def show_followup_page():
    st.title("Follow-up Aktivitas")
    
    user = st.session_state.user
    username = user['username']
    role = user['role']
    
    # Ambil data aktivitas untuk dropdown
    if role == 'superadmin':
        activities = get_all_marketing_activities()
    else:
        activities = get_marketing_activities_by_username(username)
    
    if not activities:
        st.info("Belum ada aktivitas pemasaran. Tambahkan aktivitas terlebih dahulu untuk melakukan follow-up.")
        return
        
    activities_df = pd.DataFrame(activities)
    activities_df['activity_date'] = pd.to_datetime(activities_df['activity_date'])
    activity_options = {f"{row['prospect_name']} ({row['activity_date'].strftime('%Y-%m-%d')}) - ID: {row['id']}": row['id'] 
                      for index, row in activities_df.iterrows()}
    
    selected_activity_display = st.selectbox("Pilih Aktivitas untuk Follow-up", options=list(activity_options.keys()))
    
    if selected_activity_display:
        selected_activity_id = activity_options[selected_activity_display]
        st.subheader(f"Follow-up untuk: {selected_activity_display.split(' (')[0]}")
        
        # Tampilkan follow-up yang sudah ada
        followups = get_followups_by_activity_id(selected_activity_id)
        if followups:
            st.write("**Riwayat Follow-up:**")
            followups_df = pd.DataFrame(followups)
            followups_df['followup_date'] = pd.to_datetime(followups_df['followup_date'])
            followups_df['next_followup_date'] = pd.to_datetime(followups_df['next_followup_date'])
            followups_df['created_at'] = pd.to_datetime(followups_df['created_at'])
            followups_df = followups_df.sort_values('created_at', ascending=False)
            
            display_columns = [
                'marketer_username', 'followup_date', 'notes', 'next_action', 
                'next_followup_date', 'interest_level', 'status_update', 'created_at'
            ]
            column_mapping = {
                'marketer_username': 'Marketing',
                'followup_date': 'Tanggal Follow-up',
                'notes': 'Catatan',
                'next_action': 'Tindakan Selanjutnya',
                'next_followup_date': 'Tanggal Follow-up Berikutnya',
                'interest_level': 'Tingkat Ketertarikan',
                'status_update': 'Update Status Aktivitas',
                'created_at': 'Tanggal Dibuat'
            }
            
            display_df = followups_df[display_columns].rename(columns=column_mapping)
            # Format dates for display
            display_df['Tanggal Follow-up'] = display_df['Tanggal Follow-up'].dt.strftime('%Y-%m-%d')
            display_df['Tanggal Follow-up Berikutnya'] = display_df['Tanggal Follow-up Berikutnya'].dt.strftime('%Y-%m-%d').fillna('N/A')
            display_df['Tanggal Dibuat'] = display_df['Tanggal Dibuat'].dt.strftime('%Y-%m-%d %H:%M:%S')
            # Map status update
            display_df['Update Status Aktivitas'] = display_df['Update Status Aktivitas'].map(lambda x: STATUS_MAPPING.get(x, x))
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Belum ada follow-up untuk aktivitas ini.")
            
        st.divider()
        
        # Form tambah follow-up
        st.write("**Tambah Follow-up Baru:**")
        with st.form("add_followup_form"):
            followup_date = st.date_input("Tanggal Follow-up", value=datetime.now())
            notes = st.text_area("Catatan Follow-up")
            next_action = st.text_input("Tindakan Selanjutnya")
            next_followup_date = st.date_input("Tanggal Follow-up Berikutnya (Opsional)", value=None)
            interest_level = st.select_slider("Tingkat Ketertarikan", options=["Rendah", "Sedang", "Tinggi"], value="Sedang")
            
            # Status update dropdown
            status_update_options = list(STATUS_MAPPING.values())
            # Get current status of the parent activity
            parent_activity = get_activity_by_id(selected_activity_id)
            current_status_display = STATUS_MAPPING.get(parent_activity['status'], 'Baru') if parent_activity else 'Baru'
            status_index = status_update_options.index(current_status_display) if current_status_display in status_update_options else 0
            status_update_display = st.selectbox("Update Status Aktivitas", options=status_update_options, index=status_index)
            
            submitted = st.form_submit_button("Tambah Follow-up", use_container_width=True)
            
            if submitted:
                if not all([followup_date, notes, next_action, interest_level, status_update_display]):
                    st.error("Field Tanggal Follow-up, Catatan, Tindakan Selanjutnya, Tingkat Ketertarikan, dan Update Status wajib diisi!")
                else:
                    # Map display status back to internal key
                    status_update_key = REVERSE_STATUS_MAPPING[status_update_display]
                    success, message = add_followup(
                        selected_activity_id, username, followup_date, notes, 
                        next_action, next_followup_date, interest_level, status_update_key
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

def show_user_management_page():
    st.title("Manajemen Pengguna")
    
    # Hanya superadmin yang bisa mengakses halaman ini
    if st.session_state.user['role'] != 'superadmin':
        st.error("Anda tidak memiliki akses ke halaman ini.")
        return
        
    tab1, tab2, tab3 = st.tabs(["Lihat Pengguna", "Tambah Pengguna", "Hapus Pengguna"])
    
    users = get_all_users()
    users_df = pd.DataFrame(users)
    
    with tab1:
        st.subheader("Daftar Pengguna")
        if not users_df.empty:
            display_columns = ['username', 'name', 'role', 'email', 'created_at']
            column_mapping = {
                'username': 'Username',
                'name': 'Nama Lengkap',
                'role': 'Role',
                'email': 'Email',
                'created_at': 'Tanggal Dibuat'
            }
            display_df = users_df[display_columns].rename(columns=column_mapping)
            display_df['Role'] = display_df['Role'].str.capitalize()
            # Format date
            display_df['Tanggal Dibuat'] = pd.to_datetime(display_df['Tanggal Dibuat']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Tidak ada data pengguna.")
            
    with tab2:
        st.subheader("Tambah Pengguna Baru")
        with st.form("add_user_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Konfirmasi Password", type="password")
            name = st.text_input("Nama Lengkap")
            role = st.selectbox("Role", ["marketing", "superadmin"])
            email = st.text_input("Email")
            
            submitted = st.form_submit_button("Tambah Pengguna", use_container_width=True)
            
            if submitted:
                if not all([username, password, confirm_password, name, role, email]):
                    st.error("Semua field wajib diisi!")
                elif password != confirm_password:
                    st.error("Password dan konfirmasi password tidak cocok!")
                else:
                    success, message = add_user(username, password, name, role, email)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                        
    with tab3:
        st.subheader("Hapus Pengguna")
        if not users_df.empty:
            user_options = {f"{row['name']} ({row['username']})": row['username'] 
                            for index, row in users_df.iterrows() 
                            if row['username'] != st.session_state.user['username']} # Exclude self
            
            if user_options:
                selected_user_display = st.selectbox("Pilih Pengguna untuk Dihapus", options=list(user_options.keys()))
                
                if selected_user_display:
                    selected_username = user_options[selected_user_display]
                    st.warning(f"Anda yakin ingin menghapus pengguna **{selected_user_display}**? Tindakan ini tidak dapat dibatalkan.")
                    
                    if st.button("Hapus Pengguna Ini", type="primary", use_container_width=True):
                        success, message = delete_user(selected_username, st.session_state.user['username'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.info("Tidak ada pengguna lain yang bisa dihapus.")
        else:
            st.info("Tidak ada pengguna untuk dihapus.")

def show_settings_page():
    st.title("Pengaturan")
    
    # Hanya superadmin yang bisa mengakses halaman ini
    if st.session_state.user['role'] != 'superadmin':
        st.error("Anda tidak memiliki akses ke halaman ini.")
        return
    
    # Tab untuk pengaturan umum dan backup/restore
    tab1, tab2 = st.tabs(["Pengaturan Umum", "Backup & Restore"])
    
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
                            mime="application/zip", # Correct mime type for zip
                            use_container_width=True
                        )
                else:
                    st.error(message)
        
        with col2:
            st.write("**Restore Data**")
            st.write("Restore data aplikasi dari file backup.")
            
            uploaded_file = st.file_uploader("Pilih file backup (.zip)", type=["zip"])
            
            if uploaded_file is not None:
                if st.button("Restore Data", use_container_width=True):
                    # Simpan file yang diupload sementara
                    temp_backup_path = os.path.join("temp_backup.zip")
                    with open(temp_backup_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Restore data
                    success, message = restore_data(temp_backup_path)
                    
                    # Hapus file sementara
                    if os.path.exists(temp_backup_path):
                        os.remove(temp_backup_path)
                        
                    if success:
                        st.success(message)
                        st.info("Silakan refresh halaman untuk melihat data yang sudah direstore.")
                        st.rerun() # Force rerun to reflect changes
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

def show_profile_page():
    st.title("Profil Pengguna")
    
    user = st.session_state.user
    
    st.write(f"**Username:** {user['username']}")
    st.write(f"**Nama Lengkap:** {user['name']}")
    st.write(f"**Role:** {user['role'].capitalize()}")
    st.write(f"**Email:** {user['email']}")
    
    st.divider()
    
    st.subheader("Ubah Password")
    with st.form("change_password_form"):
        current_password = st.text_input("Password Saat Ini", type="password")
        new_password = st.text_input("Password Baru", type="password")
        confirm_new_password = st.text_input("Konfirmasi Password Baru", type="password")
        
        submitted = st.form_submit_button("Ubah Password", use_container_width=True)
        
        if submitted:
            if not all([current_password, new_password, confirm_new_password]):
                st.error("Semua field wajib diisi!")
            elif new_password != confirm_new_password:
                st.error("Password baru dan konfirmasi tidak cocok!")
            else:
                # Need a function to change password in utils
                # success, message = change_password(user['username'], current_password, new_password)
                # if success:
                #     st.success(message)
                # else:
                #     st.error(message)
                st.warning("Fitur ubah password belum diimplementasikan.") # Placeholder

# Main application logic
def main():
    # Inisialisasi session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Cek login
    if not st.session_state.logged_in:
        user = check_login()
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
        # Use the settings page that includes Google Sheets integration
        # Assuming app_with_sheets.py defines show_settings_page_with_sheets
        try:
            from app_with_sheets import show_settings_page_with_sheets
            show_settings_page_with_sheets()
        except ImportError:
            st.error("Komponen pengaturan Google Sheets tidak ditemukan. Menggunakan pengaturan dasar.")
            show_settings_page() # Fallback to basic settings page
    elif menu == "Profil":
        show_profile_page()

if __name__ == "__main__":
    main()

