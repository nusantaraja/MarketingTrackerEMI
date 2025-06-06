"""
Data Hooks Module for AI Marketing Tracker

This module provides hooks to intercept data changes and trigger Google Sheets sync.
It wraps the original data functions to add sync functionality.
Includes hooks for manual sync/restore operations.
"""

import os
import yaml
from datetime import datetime
# Import the main sync instance getter
from google_sheets_sync import get_sync_instance 

# Original data functions from utils.py
from utils_with_edit_delete import (
    add_marketing_activity as original_add_marketing_activity,
    edit_marketing_activity as original_edit_marketing_activity,
    delete_marketing_activity as original_delete_marketing_activity,
    add_followup as original_add_followup,
    add_user as original_add_user,
    delete_user as original_delete_user,
    update_app_config as original_update_app_config,
    get_app_config # Needed for last sync time
)

# Constants
DATA_DIR = "data"
TABLES = ["marketing_activities", "followups", "users", "config"]

# --- Helper function for triggering sync --- 
def _trigger_incremental_sync(table_name):
    """Attempts to trigger an incremental sync for the specified table(s)."""
    print(f"Data change detected for 	{table_name}	. Triggering incremental sync...")
    try:
        sync_instance = get_sync_instance()
        if sync_instance:
            # Call sync_all_data with incremental=True. 
            # This will sync ALL tables incrementally, ensuring consistency.
            # A more targeted sync (e.g., sync_instance.sync_data(table_name, incremental=True))
            # could be implemented in google_sheets_sync.py if needed for performance.
            success, message = sync_instance.sync_all_data(incremental=True)
            if success:
                print(f"Incremental sync successful after change in 	{table_name}	.")
            else:
                print(f"Incremental sync failed after change in 	{table_name}	: {message}")
        else:
            print("Failed to get sync instance. Cannot trigger sync.")
    except Exception as e:
        print(f"Error triggering incremental sync after change in 	{table_name}	: {e}")

# --- Wrapped Data Modification Functions --- 

def add_marketing_activity(marketer_username, prospect_name, prospect_location, 
                          contact_person, contact_position, contact_phone, 
                          contact_email, activity_date, activity_type, description, status):
    """Wrapper for add_marketing_activity that triggers Google Sheets sync."""
    success, message, activity_id = original_add_marketing_activity(
        marketer_username, prospect_name, prospect_location, 
        contact_person, contact_position, contact_phone, 
        contact_email, activity_date, activity_type, description, status
    )
    if success:
        _trigger_incremental_sync("marketing_activities")
    return success, message, activity_id

def edit_marketing_activity(activity_id, prospect_name, prospect_location, 
                           contact_person, contact_position, contact_phone, 
                           contact_email, activity_date, activity_type, description, status):
    """Wrapper for edit_marketing_activity that triggers Google Sheets sync."""
    success, message = original_edit_marketing_activity(
        activity_id, prospect_name, prospect_location, 
        contact_person, contact_position, contact_phone, 
        contact_email, activity_date, activity_type, description, status
    )
    if success:
        _trigger_incremental_sync("marketing_activities")
    return success, message

def delete_marketing_activity(activity_id):
    """Wrapper for delete_marketing_activity that triggers Google Sheets sync."""
    success, message = original_delete_marketing_activity(activity_id)
    if success:
        # Sync both tables as deletion affects both
        _trigger_incremental_sync("marketing_activities and followups") 
    return success, message

def add_followup(activity_id, marketer_username, followup_date, notes, 
                next_action, next_followup_date, interest_level, status_update):
    """Wrapper for add_followup that triggers Google Sheets sync."""
    success, message = original_add_followup(
        activity_id, marketer_username, followup_date, notes, 
        next_action, next_followup_date, interest_level, status_update
    )
    if success:
        _trigger_incremental_sync("followups")
    return success, message

def add_user(username, password, name, role, email):
    """Wrapper for add_user that triggers Google Sheets sync."""
    success, message = original_add_user(username, password, name, role, email)
    if success:
        _trigger_incremental_sync("users")
    return success, message

def delete_user(username, current_username):
    """Wrapper for delete_user that triggers Google Sheets sync."""
    success, message = original_delete_user(username, current_username)
    if success:
        _trigger_incremental_sync("users")
    return success, message

def update_app_config(new_config):
    """Wrapper for update_app_config that triggers Google Sheets sync."""
    success, message = original_update_app_config(new_config)
    if success:
        # Config sync is always overwrite, handled within sync_all_data
        _trigger_incremental_sync("config") 
    return success, message

# --- Manual Sync and Restore Hooks --- 

def manual_sync_all(incremental=False):
    """Manually trigger sync of all data to Google Sheets.
    
    Args:
        incremental (bool): If True, perform incremental sync for relevant tables.
    """
    try:

        sync_instance = get_sync_instance()
        if not sync_instance:
             return False, "Failed to get Google Sheets sync instance."
        success, message = sync_instance.sync_all_data(incremental=incremental)
        return success, message 
    except Exception as e:
        return False, f"Error during manual sync: {e}"

        # FIXED: Handle tuple return (success, message) instead of dict
        success, message = sync_all()
        # Return the success status and the message from sync_all
        return success, message 
    except Exception as e:
        # Return False and the error message if an exception occurs
        return False, f"Error syncing to Google Sheets: {e}"


def manual_restore_one(table_name):
    """Manually trigger restore of a specific table from Google Sheets."""
    try:
<<<<<<< HEAD
        sync_instance = get_sync_instance()
        if not sync_instance:
             return False, "Failed to get Google Sheets sync instance."
        success, message = sync_instance.restore_data(table_name)
        return success, message
    except Exception as e:
        return False, f"Error restoring table 	{table_name}	: {e}"

def manual_restore_all(tab_name=None): 
    """Manually trigger restore of all data from Google Sheets.
       NOTE: The UI currently uses manual_restore_one. This function might be deprecated.
    """
    try:
        sync_instance = get_sync_instance()
        if not sync_instance:
             return False, "Failed to get Google Sheets sync instance."
        success, message = sync_instance.restore_all_data()
        return success, message
    except Exception as e:
        return False, f"Error restoring all data: {e}"
=======
        # FIXED: Handle tuple return (success, message) instead of dict
        success, message = restore_all(tab_name)
        # Return the success status and the message from restore_all
        return success, message
    except Exception as e:
        # Return False and the error message if an exception occurs
        return False, f"Error restoring from Google Sheets: {e}"
>>>>>>> c322489fbe8fc5503ed4811a8ba1299a9d913c72

def get_available_tabs():
    """Get a list of available tabs in the Google Sheet."""
    try:
        sync = get_sync_instance()
<<<<<<< HEAD
        if not sync or not sync.connect(): 
=======
        if not sync or not sync.connect(): # Check if sync object exists before calling connect
>>>>>>> c322489fbe8fc5503ed4811a8ba1299a9d913c72
            return False, "Failed to connect to Google Sheets.", []
        worksheets = sync.spreadsheet.worksheets()
        tab_names = [ws.title for ws in worksheets]
        return True, "Successfully retrieved tab names.", tab_names
    except Exception as e:
        return False, f"Error getting tab names: {e}", []

