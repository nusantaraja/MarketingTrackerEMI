"""
Data Hooks Module for AI Marketing Tracker

This module provides hooks to intercept data changes and trigger Google Sheets sync.
It wraps the original data functions to add sync functionality.
"""

import os
import yaml
from datetime import datetime
from google_sheets_sync import sync_on_data_change

# Original data functions from utils.py
from utils_with_edit_delete import (
    add_marketing_activity as original_add_marketing_activity,
    edit_marketing_activity as original_edit_marketing_activity,
    delete_marketing_activity as original_delete_marketing_activity,
    add_followup as original_add_followup,
    add_user as original_add_user,
    delete_user as original_delete_user,
    update_app_config as original_update_app_config
)

# Constants
DATA_DIR = "data"
TABLES = ["marketing_activities", "followups", "users", "config"]

def add_marketing_activity(marketer_username, prospect_name, prospect_location, 
                          contact_person, contact_position, contact_phone, 
                          contact_email, activity_date, activity_type, description):
    """Wrapper for add_marketing_activity that triggers Google Sheets sync."""
    # Call the original function
    success, message, activity_id = original_add_marketing_activity(
        marketer_username, prospect_name, prospect_location, 
        contact_person, contact_position, contact_phone, 
        contact_email, activity_date, activity_type, description
    )
    
    # If successful, trigger sync
    if success:
        try:
            sync_on_data_change("marketing_activities")
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
    
    return success, message, activity_id

def edit_marketing_activity(activity_id, prospect_name, prospect_location, 
                           contact_person, contact_position, contact_phone, 
                           contact_email, activity_date, activity_type, description, status):
    """Wrapper for edit_marketing_activity that triggers Google Sheets sync."""
    # Call the original function
    success, message = original_edit_marketing_activity(
        activity_id, prospect_name, prospect_location, 
        contact_person, contact_position, contact_phone, 
        contact_email, activity_date, activity_type, description, status
    )
    
    # If successful, trigger sync
    if success:
        try:
            sync_on_data_change("marketing_activities")
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
    
    return success, message

def delete_marketing_activity(activity_id):
    """Wrapper for delete_marketing_activity that triggers Google Sheets sync."""
    # Call the original function
    success, message = original_delete_marketing_activity(activity_id)
    
    # If successful, trigger sync for both activities and followups
    # (since followups related to this activity are also deleted)
    if success:
        try:
            sync_on_data_change("marketing_activities")
            sync_on_data_change("followups")
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
    
    return success, message

def add_followup(activity_id, marketer_username, followup_date, notes, 
                next_action, next_followup_date, interest_level, status_update):
    """Wrapper for add_followup that triggers Google Sheets sync."""
    # Call the original function
    success, message = original_add_followup(
        activity_id, marketer_username, followup_date, notes, 
        next_action, next_followup_date, interest_level, status_update
    )
    
    # If successful, trigger sync
    if success:
        try:
            sync_on_data_change("followups")
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
    
    return success, message

def add_user(username, password, name, role, email):
    """Wrapper for add_user that triggers Google Sheets sync."""
    # Call the original function
    success, message = original_add_user(username, password, name, role, email)
    
    # If successful, trigger sync
    if success:
        try:
            sync_on_data_change("users")
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
    
    return success, message

def delete_user(username, current_username):
    """Wrapper for delete_user that triggers Google Sheets sync."""
    # Call the original function
    success, message = original_delete_user(username, current_username)
    
    # If successful, trigger sync
    if success:
        try:
            sync_on_data_change("users")
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
    
    return success, message

def update_app_config(new_config):
    """Wrapper for update_app_config that triggers Google Sheets sync."""
    # Call the original function
    success, message = original_update_app_config(new_config)
    
    # If successful, trigger sync
    if success:
        try:
            sync_on_data_change("config")
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")
    
    return success, message

# Additional utility functions for manual sync and restore

def manual_sync_all():
    """Manually trigger sync of all data to Google Sheets."""
    from google_sheets_sync import sync_all
    try:
        results = sync_all()
        success = all(results.values())
        if success:
            return True, "All data successfully synced to Google Sheets."
        else:
            failed = [table for table, result in results.items() if not result]
            return False, f"Failed to sync some tables: {', '.join(failed)}"
    except Exception as e:
        return False, f"Error syncing to Google Sheets: {e}"

def manual_restore_all(tab_name=None):
    """Manually trigger restore of all data from Google Sheets."""
    from google_sheets_sync import restore_all
    try:
        results = restore_all(tab_name)
        success = all(results.values())
        if success:
            return True, "All data successfully restored from Google Sheets."
        else:
            failed = [table for table, result in results.items() if not result]
            return False, f"Failed to restore some tables: {', '.join(failed)}"
    except Exception as e:
        return False, f"Error restoring from Google Sheets: {e}"

def get_available_tabs():
    """Get a list of available tabs in the Google Sheet."""
    from google_sheets_sync import get_sync_instance
    try:
        sync = get_sync_instance()
        if not sync.connect():
            return False, "Failed to connect to Google Sheets.", []
        
        worksheets = sync.spreadsheet.worksheets()
        tab_names = [ws.title for ws in worksheets]
        return True, "Successfully retrieved tab names.", tab_names
    except Exception as e:
        return False, f"Error getting tab names: {e}", []
