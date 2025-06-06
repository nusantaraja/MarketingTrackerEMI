import yaml
import os
import bcrypt
import uuid
from datetime import datetime
import pytz # Import pytz
import streamlit as st

# Constants
DATA_DIR = "data"
ACTIVITIES_FILENAME = "marketing_activities.yaml"
USERS_FILENAME = "users.yaml"
FOLLOWUPS_FILENAME = "followups.yaml"
CONFIG_FILENAME = "config.yaml"
WIB_TZ = pytz.timezone("Asia/Bangkok") # Define WIB timezone (UTC+7)

# --- File I/O --- 

def create_yaml_if_not_exists(file_path, default_content):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            yaml.dump(default_content, file, default_flow_style=False, allow_unicode=True)
        print(f"Created default file: {file_path}")

def read_yaml(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error reading YAML file {file_path}: {e}")
            # Return a default structure or None based on expected usage
            if ACTIVITIES_FILENAME in file_path:
                return {"marketing_activities": []}
            elif USERS_FILENAME in file_path:
                return {"users": []}
            elif FOLLOWUPS_FILENAME in file_path:
                return {"followups": []}
            elif CONFIG_FILENAME in file_path:
                return {}
            else:
                return None
    return None

def write_yaml(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except Exception as e:
        print(f"Error writing YAML file {file_path}: {e}")
# --- Database Initialization ---
        if hasattr(st, "error"): # Check if streamlit context exists
             st.error(f"Gagal menyimpan data ke {os.path.basename(file_path)}.")

# --- Added function for validation script --- 
def write_yaml_data(table_name, data):
    """Writes data to the specified table's YAML file."""
    filename_map = {
        "marketing_activities": ACTIVITIES_FILENAME,
        "users": USERS_FILENAME,
        "followups": FOLLOWUPS_FILENAME,
        "config": CONFIG_FILENAME
    }
    filename = filename_map.get(table_name)
    if not filename:
        print(f"Error: Unknown table name 	{table_name}	 for writing YAML data.")
        return
    file_path = os.path.join(DATA_DIR, filename)
    write_yaml(file_path, data)
def read_yaml_data(table_name):
        st.error(f"Gagal menyimpan data ke {os.path.basename(file_path)}.")
    

# --- Security --- 

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password, hashed_password):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        # Handle cases where the hash might be invalid (e.g., not bcrypt)
        print(f"Warning: Invalid hash format encountered for password verification.")
        return False

# --- Utilities --- 

def generate_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def get_wib_now_str(): # Renamed for clarity
    """Returns the current time in WIB as a formatted string."""
    now_wib = datetime.now(WIB_TZ)
    return now_wib.strftime("%Y-%m-%d %H:%M:%S")

def get_current_timestamp():
    # Get current time in WIB
    now_wib = datetime.now(WIB_TZ)
    return now_wib.strftime("%Y-%m-%d %H:%M:%S") # Format as string


# --- Database Initialization --- 

def initialize_database():
    print("Initializing database files...")
    # File users.yaml
    users_file = os.path.join(DATA_DIR, USERS_FILENAME)
    default_users = {
        "users": [
            {
                "id": generate_id("usr"), # Add ID for consistency
                "username": "admin",
                "password_hash": hash_password("admin123"),
                "name": "Admin Utama",
                "role": "superadmin",
                "email": "admin@example.com",
                "created_at": get_wib_now_str() # Use WIB timestamp
            }
        ]
    }    
    create_yaml_if_not_exists(users_file, default_users)
    
    # File marketing_activities.yaml
    activities_file = os.path.join(DATA_DIR, ACTIVITIES_FILENAME)
    default_activities = {"marketing_activities": []} 
    create_yaml_if_not_exists(activities_file, default_activities)
    # Check and migrate old key if necessary
    _migrate_activities_key(activities_file)
    
    # File followups.yaml
    followups_file = os.path.join(DATA_DIR, FOLLOWUPS_FILENAME)
    default_followups = {"followups": []}
    create_yaml_if_not_exists(followups_file, default_followups)
    
    # File config.yaml
    config_file = os.path.join(DATA_DIR, CONFIG_FILENAME)
    # Using a simpler key-value structure for config as expected by sync module
    default_config = {
        "app_name": "AI Suara Marketing Tracker",
        "company_name": "AI Suara",
        "version": "1.0.3", # Incremented version for status add feature
        "theme": "light",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "enable_email": False,
        "enable_reminder": True,
        "reminder_days_before": 1
    }
    create_yaml_if_not_exists(config_file, default_config)
    print("Database initialization complete.")

# --- Migration Helper --- 

def _migrate_activities_key(activities_file):
    """Checks for old "activities" key and migrates to "marketing_activities"."""
    activities_data = read_yaml(activities_file)
    if activities_data and "activities" in activities_data and "marketing_activities" not in activities_data:
        print(f"Migrating old 'activities' key to 'marketing_activities' in {activities_file}...")
        activities_data["marketing_activities"] = activities_data.pop("activities")
        write_yaml(activities_file, activities_data)
        print("Migration complete.")
        return True
    return False

# --- User Management --- 

def authenticate_user(username, password):
    users_file = os.path.join(DATA_DIR, USERS_FILENAME)
    users_data = read_yaml(users_file)
    if not users_data or "users" not in users_data:
        return None
    for user in users_data["users"]:
        if user["username"] == username and verify_password(password, user["password_hash"]):
            return user
    return None

def get_all_users():
    users_file = os.path.join(DATA_DIR, USERS_FILENAME)
    users_data = read_yaml(users_file)
    if not users_data or "users" not in users_data:
        return []
    return users_data["users"]

def add_user(username, password, name, role, email):
    users_file = os.path.join(DATA_DIR, USERS_FILENAME)
    users_data = read_yaml(users_file)
    if not users_data or "users" not in users_data:
        users_data = {"users": []}
    if any(user["username"] == username for user in users_data["users"]):
        return False, "Username sudah digunakan"
    new_user = {
        "id": generate_id("usr"), # Add ID
        "username": username,
        "password_hash": hash_password(password),
        "name": name,
        "role": role,
        "email": email,
        "created_at": get_wib_now_str() # Use WIB timestamp

        "created_at": get_current_timestamp() # Use WIB timestamp

    }
    users_data["users"].append(new_user)
    write_yaml(users_file, users_data)
    return True, "Pengguna berhasil ditambahkan"

def delete_user(username, current_user_username):
    if username == current_user_username:
        return False, "Anda tidak dapat menghapus akun Anda sendiri"
    users_file = os.path.join(DATA_DIR, USERS_FILENAME)
    users_data = read_yaml(users_file)
    if not users_data or "users" not in users_data:
        return False, "Data pengguna tidak ditemukan"
    initial_length = len(users_data["users"])
    users_data["users"] = [user for user in users_data["users"] if user["username"] != username]
    if len(users_data["users"]) == initial_length:
        return False, "Pengguna tidak ditemukan"
    write_yaml(users_file, users_data)
    return True, f"Pengguna {username} berhasil dihapus"

# --- Marketing Activities --- 

def get_all_marketing_activities():
    activities_file = os.path.join(DATA_DIR, ACTIVITIES_FILENAME)
    # Ensure migration check happens if needed
    _migrate_activities_key(activities_file)
    activities_data = read_yaml(activities_file)
    if not activities_data or "marketing_activities" not in activities_data:
        return []
    return activities_data["marketing_activities"]

def get_marketing_activities_by_username(username):
    activities = get_all_marketing_activities()
    return [activity for activity in activities if activity["marketer_username"] == username]

# Updated function signature to include status
def add_marketing_activity(marketer_username, prospect_name, prospect_location, 
                          contact_person, contact_position, contact_phone, 
                          contact_email, activity_date, activity_type, description, status):
    activities_file = os.path.join(DATA_DIR, ACTIVITIES_FILENAME)
    # Ensure migration check happens if needed
    _migrate_activities_key(activities_file)
    activities_data = read_yaml(activities_file)
    if not activities_data or "marketing_activities" not in activities_data:
        activities_data = {"marketing_activities": []}
    activity_id = generate_id("act")

    current_time_wib = get_wib_now_str() # Get WIB timestamp

    current_time_wib = get_current_timestamp() # Get WIB timestamp

    new_activity = {
        "id": activity_id,
        "marketer_username": marketer_username,
        "prospect_name": prospect_name,
        "prospect_location": prospect_location,
        "contact_person": contact_person,
        "contact_position": contact_position,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
        "activity_date": str(activity_date), # Ensure date is string
        "activity_type": activity_type,
        "description": description,
        "status": status, # Use the status passed from the form
        "created_at": current_time_wib, # Use WIB timestamp
        "updated_at": current_time_wib # Use WIB timestamp
    }
    activities_data["marketing_activities"].append(new_activity)
    write_yaml(activities_file, activities_data)
    return True, "Aktivitas pemasaran berhasil ditambahkan", activity_id

def edit_marketing_activity(activity_id, prospect_name, prospect_location, 
                           contact_person, contact_position, contact_phone, 
                           contact_email, activity_date, activity_type, description, status):
    activities_file = os.path.join(DATA_DIR, ACTIVITIES_FILENAME)
    _migrate_activities_key(activities_file) # Ensure migration check
    activities_data = read_yaml(activities_file)
    if not activities_data or "marketing_activities" not in activities_data:
        return False, "Data aktivitas tidak ditemukan"
    activity_found = False
    for activity in activities_data["marketing_activities"]:
        if activity["id"] == activity_id:
            activity_found = True
            activity.update({
                "prospect_name": prospect_name,
                "prospect_location": prospect_location,
                "contact_person": contact_person,
                "contact_position": contact_position,
                "contact_phone": contact_phone,
                "contact_email": contact_email,
                "activity_date": str(activity_date), # Ensure date is string
                "activity_type": activity_type,
                "description": description,
                "status": status,

                "updated_at": get_wib_now_str() # Use WIB timestamp for update

                "updated_at": get_current_timestamp() # Use WIB timestamp for update

            })
            break
    if not activity_found:
        return False, "Aktivitas tidak ditemukan"
    write_yaml(activities_file, activities_data)
    return True, "Aktivitas pemasaran berhasil diperbarui"

def delete_marketing_activity(activity_id):
    activities_file = os.path.join(DATA_DIR, ACTIVITIES_FILENAME)
    _migrate_activities_key(activities_file) # Ensure migration check
    activities_data = read_yaml(activities_file)
    if not activities_data or "marketing_activities" not in activities_data:
        return False, "Data aktivitas tidak ditemukan"
    initial_length = len(activities_data["marketing_activities"])
    activities_data["marketing_activities"] = [act for act in activities_data["marketing_activities"] if act["id"] != activity_id]
    if len(activities_data["marketing_activities"]) == initial_length:
        return False, "Aktivitas tidak ditemukan"
    write_yaml(activities_file, activities_data)
    # Delete related followups
    followups_file = os.path.join(DATA_DIR, FOLLOWUPS_FILENAME)
    followups_data = read_yaml(followups_file)
    if followups_data and "followups" in followups_data:
        followups_data["followups"] = [f for f in followups_data["followups"] if f["activity_id"] != activity_id]
        write_yaml(followups_file, followups_data)
    return True, "Aktivitas pemasaran berhasil dihapus"

def update_activity_status(activity_id, new_status):
    activities_file = os.path.join(DATA_DIR, ACTIVITIES_FILENAME)
    _migrate_activities_key(activities_file) # Ensure migration check
    activities_data = read_yaml(activities_file)
    if not activities_data or "marketing_activities" not in activities_data:
        return False, "Data aktivitas tidak ditemukan"
    activity_found = False
    for activity in activities_data["marketing_activities"]:
        if activity["id"] == activity_id:
            activity["status"] = new_status

            activity["updated_at"] = get_wib_now_str() # Use WIB timestamp for update

            activity["updated_at"] = get_current_timestamp() # Use WIB timestamp for update

            activity_found = True
            break
    if not activity_found:
        return False, "Aktivitas tidak ditemukan"
    write_yaml(activities_file, activities_data)
    return True, "Status aktivitas berhasil diperbarui"

def get_activity_by_id(activity_id):
    activities = get_all_marketing_activities()
    for activity in activities:
        if activity["id"] == activity_id:
            return activity
    return None

# --- Follow-ups --- 

def get_all_followups():
    followups_file = os.path.join(DATA_DIR, FOLLOWUPS_FILENAME)
    followups_data = read_yaml(followups_file)
    if not followups_data or "followups" not in followups_data:
        return []
    return followups_data["followups"]

def get_followups_by_activity_id(activity_id):
    followups = get_all_followups()
    return [followup for followup in followups if followup["activity_id"] == activity_id]

def get_followups_by_username(username):
    followups = get_all_followups()
    return [followup for followup in followups if followup["marketer_username"] == username]

def add_followup(activity_id, marketer_username, followup_date, notes, 
                next_action, next_followup_date, interest_level, status_update):
    followups_file = os.path.join(DATA_DIR, FOLLOWUPS_FILENAME)
    followups_data = read_yaml(followups_file)
    if not followups_data or "followups" not in followups_data:
        followups_data = {"followups": []}
    followup_id = generate_id("fu")
    new_followup = {
        "id": followup_id,
        "activity_id": activity_id,
        "marketer_username": marketer_username,
        "followup_date": str(followup_date), # Ensure date is string
        "notes": notes,
        "next_action": next_action,
        "next_followup_date": str(next_followup_date) if next_followup_date else None, # Ensure date is string or None
        "interest_level": interest_level,
        "status_update": status_update,

        "created_at": get_wib_now_str() # Use WIB timestamp

        "created_at": get_current_timestamp() # Use WIB timestamp

    }
    followups_data["followups"].append(new_followup)
    write_yaml(followups_file, followups_data)
    # Update parent activity status
    update_activity_status(activity_id, status_update)
    return True, "Follow-up berhasil ditambahkan"

# --- Configuration --- 

def get_app_config():
    config_file = os.path.join(DATA_DIR, CONFIG_FILENAME)
    config_data = read_yaml(config_file)
    # Return default if file is missing or empty
    if not config_data:
        print(f"Warning: Config file {config_file} not found or empty. Using defaults.")
        return {
            "app_name": "AI Suara Marketing Tracker",
            "company_name": "AI Suara",
            "version": "1.0.3",
            "theme": "light",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "enable_email": False,
            "enable_reminder": True,
            "reminder_days_before": 1
        }
    return config_data

def update_app_config(new_config_subset):
    config_file = os.path.join(DATA_DIR, CONFIG_FILENAME)
    current_config = get_app_config() # Get current or default config
    current_config.update(new_config_subset) # Update with new values
    write_yaml(config_file, current_config)

    return True, "Konfigurasi aplikasi berhasil diperbarui"


    return True, "Konfigurasi berhasil diperbarui"

# --- Session Management (Simplified) ---

def login(username, password):
    user = authenticate_user(username, password)
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None

def check_login():
    if st.session_state.get("logged_in", False):
        return st.session_state.user
    return None


