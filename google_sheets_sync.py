"""
Google Sheets Sync Module for AI Marketing Tracker (Adapted for Specific Template)

This module handles synchronization between the local application data and Google Sheets,
assuming dedicated sheets (
    'Activities', 'Followups', 'Users', 'Config') exist
as per the provided template.
"""

import os
import gspread
import yaml
import pandas as pd
from datetime import datetime
import pytz # Import pytz
import streamlit as st
import uuid  # For generating user IDs if missing
import re # For cleaning phone numbers

# Constants
# Use the user-provided ID
SPREADSHEET_ID = "1IRZ6iLmE62lPyiv8sJqLMQBH66fci7L-H9NuGiscMvo"
CREDENTIALS_FILE = "service_account_key.json"
DATA_DIR = "data"
WIB_TZ = pytz.timezone("Asia/Bangkok") # Define WIB timezone (UTC+7)

# Map internal table names to actual Google Sheet names
# Ensure these sheet names exactly match the tabs in your Google Sheet
TABLE_MAP = {
    "marketing_activities": "Activities",
    "followups": "Followups",
    "users": "Users",
    "config": "Config"
}

# Define the expected headers based on the template analysis (data_mapping.md)
# The order MUST match the column order in the Google Sheet template
EXPECTED_HEADERS = {
    "marketing_activities": [  # Matches 'Activities' sheet
        'id', 'marketer_username', 'prospect_name', 'prospect_location',
        'contact_person', 'contact_position', 'contact_phone', 'contact_email',
        'activity_date', 'activity_type', 'description', 'status',
        'created_at', 'updated_at'
    ],
    "followups": [  # Matches 'Followups' sheet
        'id', 'activity_id', 'marketer_username', 'followup_date', 'notes',
        'next_action', 'next_followup_date', 'interest_level', 'status_update',
        'created_at'
    ],
    "users": [  # Matches 'Users' sheet
        'id', 'username', 'password_hash', 'name', 'role', 'email', 'created_at'
    ],
    "config": [  # Matches 'Config' sheet
        'Key', 'Value'  # Corrected from template analysis
    ]
}

# Define date/timestamp columns for specific formatting
DATE_COLUMNS = {
    "marketing_activities": ['activity_date'],
    "followups": ['followup_date', 'next_followup_date']
}
TIMESTAMP_COLUMNS = {
    "marketing_activities": ['created_at', 'updated_at'],
    "followups": ['created_at'],
    "users": ['created_at']
}

class GoogleSheetsSync:
    def __init__(self, credentials_file=CREDENTIALS_FILE, spreadsheet_id=SPREADSHEET_ID):
        """Initialize the Google Sheets sync module."""
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self.connect()

    def connect(self):
        """Connect to Google Sheets API using Streamlit Secrets or local file."""
        # Avoid reconnecting if already connected
        if self.client and self.spreadsheet:
            try:
                # Simple check: list worksheets
                self.spreadsheet.worksheets()
                print("Existing connection seems valid.")
                return True
            except Exception as conn_err:
                print(f"Existing connection check failed: {conn_err}. Reconnecting...")
                self.client = None
                self.spreadsheet = None

        print("Attempting to connect to Google Sheets...")
        try:
            creds_source = None
            # Try Streamlit Secrets first
            if hasattr(st, 'secrets') and "google_credentials" in st.secrets:
                print("Authenticating using Streamlit Secrets...")
                creds_dict = dict(st.secrets["google_credentials"])
                self.client = gspread.service_account_from_dict(creds_dict)
                creds_source = "Streamlit Secrets"
            # Fallback to local file
            elif os.path.exists(self.credentials_file):
                print(
                    f"Authenticating using local file: {self.credentials_file}..."
                )
                self.client = gspread.service_account(
                    filename=self.credentials_file)
                creds_source = f"Local file ({self.credentials_file})"
            else:
                print("Error: Google credentials not found.")
                # Avoid showing error in UI if running locally without secrets
                if hasattr(st, 'secrets'):
                    st.error("Google Sheets credentials configuration missing.")
                return False

            print(f"Successfully authenticated using {creds_source}.")
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            print(
                f"Successfully connected to Google Sheet: {self.spreadsheet.title}"
            )
            # Verify required sheets exist
            self._verify_sheets_exist()
            return True

        except gspread.exceptions.APIError as e:
            print(f"Google Sheets API Error: {e}")
            if hasattr(st, 'secrets'):
                st.error(
                    f"Google Sheets API Error: {e}. Check permissions or API enablement."
                )
            return False
        except FileNotFoundError:
            print(
                f"Error: Credentials file not found at {self.credentials_file}."
            )
            if hasattr(st, 'secrets'):
                st.error(
                    f"Credentials file not found at {self.credentials_file}."
                )
            return False
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            if hasattr(st, 'secrets'):
                st.error(
                    f"An unexpected error occurred connecting to Google Sheets: {e}"
                )
            return False

    def get_current_month_tab_name(self):
        """Returns the current month's tab name in YYYY_MM format."""
        # Use WIB for consistency if needed, though only format matters here
        now_wib = datetime.now(WIB_TZ)
        return now_wib.strftime("%Y_%m")

    def _verify_sheets_exist(self):
        """Verify that all required sheets exist in the spreadsheet."""
        if not self.spreadsheet:
            print("Spreadsheet object not available for verification.")
            return
        try:
            existing_sheet_titles = [sheet.title for sheet in self.spreadsheet.worksheets()]
            missing_sheets = []
            for internal_name, actual_name in TABLE_MAP.items():
                if actual_name not in existing_sheet_titles:
                    missing_sheets.append(actual_name)
                    print(
                        f"Warning: Required sheet '{actual_name}' not found in the Google Sheet."
                    )
            if missing_sheets:
                if hasattr(st, 'secrets'):
                    st.warning(
                        f"The following required sheets are missing in your Google Sheet '{self.spreadsheet.title}': {', '.join(missing_sheets)}. Please ensure they exist and match the template."
                    )
            else:
                print("All required sheets found.")
        except Exception as e:
            print(f"Error verifying sheets: {e}")
            if hasattr(st, 'secrets'):
                st.error(
                    f"Could not verify the existence of required sheets: {e}"
                )

    def _get_target_sheet(self, table_name):
        """Get the gspread worksheet object for the given internal table name."""
        if not self.spreadsheet:
            print("Cannot get target sheet, not connected.")
            if not self.connect():  # Try reconnecting
                if hasattr(st, 'secrets'):
                    st.error("Failed to connect to Google Sheets.")
                return None
            if not self.spreadsheet:
                if hasattr(st, 'secrets'):
                    st.error(
                        "Connection re-established, but spreadsheet object missing."
                    )
                return None

        target_sheet_name = TABLE_MAP.get(table_name)
        if not target_sheet_name:
            print(
                f"Error: No sheet mapping found for internal table name '{table_name}'."
            )
            if hasattr(st, 'secrets'):
                st.error(
                    f"Configuration error: Sheet mapping missing for {table_name}."
                )
            return None

        try:
            worksheet = self.spreadsheet.worksheet(target_sheet_name)
            print(f"Accessed worksheet: '{target_sheet_name}'")
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            print(
                f"Error: Worksheet '{target_sheet_name}' not found in the spreadsheet."
            )
            if hasattr(st, 'secrets'):
                st.error(
                    f"Worksheet '{target_sheet_name}' not found. Please ensure it exists and the name matches exactly."
                )
            return None
        except Exception as e:
            print(f"Error accessing worksheet '{target_sheet_name}': {e}")
            if hasattr(st, 'secrets'):
                st.error(f"Error accessing worksheet '{target_sheet_name}': {e}")
            return None

    def _format_value(self, value, header, table_name):
        """Formats value based on header and table type for Google Sheets.
           Forces dates/timestamps and phone numbers to be treated as text.
           Ensures timestamps reflect WIB (as stored in YAML).
        """
        # Handle None or empty strings
        if value is None or value == '':
            return ''
        
        # Phone number formatting: Return as string to preserve leading zeros
        if table_name == 'marketing_activities' and header == 'contact_phone':
            # Prepend single quote to force text format in Sheets
            return "'" + str(value)
            
        # Date formatting: Format and prepend quote to force text
        if header in DATE_COLUMNS.get(table_name, []):
            try:
                if isinstance(value, datetime):
                    # This case might not happen often if YAML stores strings
                    formatted_date = value.strftime('%Y-%m-%d')
                else:
                    # Try parsing common date formats from string
                    dt_obj = datetime.strptime(str(value).split(' ')[0], '%Y-%m-%d') # Handle potential time part
                    formatted_date = dt_obj.strftime('%Y-%m-%d')
                return "'" + formatted_date # Prepend quote
            except ValueError:
                print(f"Warning: Could not parse date '{value}' for header '{header}'. Sending as quoted string.")
                return "'" + str(value) # Send as quoted string if parsing fails
            except Exception as e:
                 print(f"Warning: Error formatting date '{value}' for header '{header}': {e}. Sending as quoted string.")
                 return "'" + str(value)

        # Timestamp formatting: Format (as WIB string from YAML) and prepend quote to force text
        if header in TIMESTAMP_COLUMNS.get(table_name, []):
            try:
                # Value from YAML should already be a WIB string like 'YYYY-MM-DD HH:MM:SS'
                timestamp_str = str(value)
                # Optional: Validate the format before sending?
                try:
                    datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    # Format is valid, prepend quote
                    return "'" + timestamp_str
                except ValueError:
                    print(f"Warning: Timestamp string '{timestamp_str}' from YAML for header '{header}' does not match expected format '%Y-%m-%d %H:%M:%S'. Sending as is (quoted).")
                    return "'" + timestamp_str # Send as quoted string anyway

            except Exception as e:
                 print(f"Warning: Error formatting timestamp '{value}' for header '{header}': {e}. Sending as quoted string.")
                 return "'" + str(value)

        # Default: return as string (without quote unless specified above)
        return str(value)

    def sync_data(self, table_name):
        """Sync data from a specific table's YAML file to its dedicated Google Sheet."""
        print(f"Starting sync for table: {table_name}")
        worksheet = self._get_target_sheet(table_name)
        if not worksheet:
            return False, f"Target sheet for {table_name} not found." # Return message

        file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
        if not os.path.exists(file_path):
            print(
                f"Data file not found: {file_path}, skipping sync for {table_name}."
            )
            # Return True, message? Or False? Let's return False as data is missing.
            return False, f"Data file {file_path} not found."

        # Read data from YAML, handling the root key structure
        data_to_sync = []
        config_data_dict = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_data = yaml.safe_load(file)

            if raw_data is None:
                print(f"YAML file {file_path} is empty.")
                data_to_sync = [] if table_name != 'config' else {}
            elif table_name == 'config':
                if isinstance(raw_data, dict):
                    config_data_dict = raw_data
                else:
                    print(
                        f"Warning: Expected dict structure for config.yaml, found {type(raw_data)}."
                    )
                    return False, "Invalid config.yaml format." # Return message
            elif isinstance(raw_data, dict) and table_name in raw_data:
                data_to_sync = raw_data[table_name]
                if not isinstance(data_to_sync, list):
                    print(
                        f"Warning: Expected list under key '{table_name}' in {file_path}, found {type(data_to_sync)}."
                    )
                    data_to_sync = []  # Treat as empty if structure is wrong
            elif isinstance(raw_data, list):
                # Allow direct list structure as fallback?
                print(
                    f"Warning: Reading direct list from {file_path}. Expected dict with key '{table_name}'."
                )
                data_to_sync = raw_data
            else:
                print(
                    f"Warning: Unexpected YAML structure in {file_path}. Cannot sync."
                )
                return False, f"Unexpected YAML structure in {file_path}." # Return message

        except Exception as e:
            print(f"Error reading or parsing YAML file {file_path}: {e}")
            if hasattr(st, 'secrets'):
                st.error(f"Error reading data file for {table_name}: {e}")
            return False, f"Error reading YAML file {file_path}." # Return message

        # Get the expected headers for this sheet
        expected_headers = EXPECTED_HEADERS.get(table_name)
        if not expected_headers:
            print(f"Error: No expected headers defined for table '{table_name}'.")
            if hasattr(st, 'secrets'):
                st.error(f"Configuration error: Headers missing for {table_name}."
                         )
            return False, f"Headers missing for {table_name}." # Return message

        # --- Sync Logic --- 
        try:
            if table_name == 'config':
                # Config: Overwrite sheet with key-value pairs
                print(
                    f"Syncing config data (overwrite) to sheet '{TABLE_MAP[table_name]}'."
                )
                values_to_update = [expected_headers]  # Start with header row
                for key, value in config_data_dict.items():
                    # Ensure strings
                    values_to_update.append([str(key), str(value)])

                worksheet.clear()
                # Use USER_ENTERED here, formatting is handled by _format_value if needed
                worksheet.update(f'A1:B{len(values_to_update)}',
                                 values_to_update,
                                 value_input_option='USER_ENTERED') 
                msg = f"Successfully synced {len(values_to_update)-1} config items."
                print(msg)
                return True, msg # Return success and message

            else:
                # Activities, Followups, Users: Append new data
                print(
                    f"Syncing {table_name} data (append) to sheet '{TABLE_MAP[table_name]}'."
                )
                if not data_to_sync:  # Check if list is empty
                    msg = f"No data entries found in {file_path} for {table_name}. Nothing to append."
                    print(msg)
                    return True, msg  # Not an error, just nothing to do

                # Check if sheet is empty or only has headers
                all_vals = worksheet.get_all_values()
                # Consider empty or only header row
                is_sheet_empty = len(all_vals) <= 1

                if is_sheet_empty:
                    print(
                        f"Sheet '{TABLE_MAP[table_name]}' appears empty. Writing headers first."
                    )
                    try:
                        # Write headers normally
                        worksheet.update('A1',
                                         [expected_headers],
                                         value_input_option='USER_ENTERED')
                    except Exception as header_err:
                        msg = f"Error writing headers to empty sheet '{TABLE_MAP[table_name]}': {header_err}"
                        print(msg)
                        if hasattr(st, 'secrets'):
                            st.error(
                                f"Could not initialize headers for sheet '{TABLE_MAP[table_name]}': {header_err}"
                            )
                        return False, msg  # Stop if headers can't be written

                # Prepare data rows in the correct order
                rows_to_append = []
                for item in data_to_sync:
                    if not isinstance(item, dict):
                        print(
                            f"Warning: Skipping non-dict item in {table_name} data: {item}"
                        )
                        continue

                    # Special handling for 'users' ID generation if missing
                    if table_name == 'users' and 'id' not in item:
                        item['id'] = f"usr-{uuid.uuid4().hex[:8]}"
                        print(
                            f"Generated missing ID for user: {item['username']} -> {item['id']}"
                        )
                        # Note: This generated ID is only for the sheet, not saved back to YAML

                    # Prepare row values, formatting specific columns using _format_value
                    row_values = []
                    for header in expected_headers:
                        value = item.get(header, "")
                        formatted_value = self._format_value(value, header, table_name)
                        row_values.append(formatted_value)
                            
                    rows_to_append.append(row_values)

                if not rows_to_append:
                    msg = f"No valid data rows prepared for {table_name}. Nothing to append."
                    print(msg)
                    return True, msg

                # Append data rows to the sheet
                print(
                    f"Appending {len(rows_to_append)} rows to sheet '{TABLE_MAP[table_name]}'."
                )
                # Use USER_ENTERED. The prepended quote in _format_value handles text forcing.
                worksheet.append_rows(rows_to_append,
                                      value_input_option='USER_ENTERED',
                                      insert_data_option='INSERT_ROWS',
                                      table_range='A1')  # Append after last row with data
                msg = f"Successfully appended {len(rows_to_append)} rows for {table_name}."
                print(msg)

                # **Important Limitation:** This append logic assumes that the YAML file *only* contains 
                # *new* records since the last sync. If the YAML file contains *all* records, 
                # this will create duplicates in the sheet. 
                # A more robust sync would require reading existing IDs from the sheet 
                # and only appending/updating records that are new or changed.
                # For now, we proceed with the simple append as requested by the apparent need.
                if hasattr(st, 'secrets'):
                    st.warning(
                        f"Synced {table_name} by appending. Ensure YAML only contains new data to avoid duplicates."
                    )  # Inform user
                return True, msg # Return success and message

        except gspread.exceptions.APIError as e:
            msg = f"Google Sheets API Error syncing {table_name}: {e}"
            print(msg)
            if hasattr(st, 'secrets'):
                st.error(msg)
            return False, msg # Return error and message
        except Exception as e:
            msg = f"Unexpected error during sync for {table_name}: {e}"
            print(msg)
            if hasattr(st, 'secrets'):
                st.error(
                    f"An unexpected error occurred while syncing {table_name}: {e}"
                )
            return False, msg # Return error and message

    def sync_all_data(self):
        """Sync all tables based on the TABLE_MAP."""
        if not self.spreadsheet:
            print("Not connected. Cannot sync all data.")
            if not self.connect(): return False, "Failed to connect"
            if not self.spreadsheet: return False, "Spreadsheet object missing after connect"

        results = {}
        print("Starting sync for all mapped tables...")
        if hasattr(st, 'secrets'): st.info("Starting sync for all tables...")
        all_success = True
        error_messages = []
        success_messages = []
        for table_name in TABLE_MAP.keys():  # Iterate through internal names
            print(f"--- Syncing {table_name} to sheet '{TABLE_MAP[table_name]}' ---")
            # **CRITICAL CHANGE:** The current implementation syncs the *entire* YAML content.
            # For append-style sheets (Activities, Followups, Users), this will cause duplicates!
            # The sync_data function needs to be smarter (read sheet, compare, update/append).
            # For now, sticking to the simple (but potentially duplicate-creating) sync.
            sync_success, msg = self.sync_data(table_name)
            results[table_name] = sync_success
            print(f"--- Finished syncing {table_name} (Success: {sync_success}) ---")
            if sync_success:
                success_messages.append(f"{table_name}: {msg}")
            else:
                all_success = False
                error_messages.append(f"{table_name}: {msg}")
                if hasattr(st, 'secrets'): st.warning(f"Sync failed for {table_name}: {msg}")

        print("Finished syncing all tables.")
        final_message = ""
        if all_success:
            final_message = f"Finished syncing all tables. Details: {'; '.join(success_messages)}"
            if hasattr(st, 'secrets'): st.success(final_message)
        else:
            final_message = f"Finished syncing all tables, but some tables failed: {'; '.join(error_messages)}"
            if hasattr(st, 'secrets'): st.error(final_message)
        return all_success, final_message

    def restore_data(self, table_name):
        """Restore data from a dedicated Google Sheet to its local YAML file."""
        print(f"Starting restore for table: {table_name}")
        worksheet = self._get_target_sheet(table_name)
        if not worksheet:
            return False, f"Target sheet for {table_name} not found."

        try:
            print(f"Fetching all records from sheet '{TABLE_MAP[table_name]}'.")
            # Use get_all_records for structured data, assumes header row exists
            sheet_data = worksheet.get_all_records()
            print(f"Successfully fetched {len(sheet_data)} records.")

            # Process fetched data into YAML structure
            if table_name == "config":
                # Convert list of {'Key': k, 'Value': v} dicts back to simple {k: v} dict
                restored_data_dict = {str(row.get('Key', '')): str(row.get('Value', '')) for row in sheet_data if row.get('Key')}
                final_restored_data = restored_data_dict
            else:
                # For other tables, the structure is { 'table_name': [...] }
                # Ensure data types are handled correctly if needed (e.g., numbers)
                # For now, keep as strings as read by get_all_records
                # Convert keys to lowercase to match YAML expectations if needed
                restored_list = []
                expected_keys = EXPECTED_HEADERS.get(table_name, [])
                for record in sheet_data:
                    # Ensure all expected keys exist, even if empty
                    # Remove the prepended quote if present from dates/timestamps/phones during restore
                    processed_record = {}
                    for key in expected_keys:
                        value = str(record.get(key, ""))
                        if value.startswith("'"):
                            processed_record[key] = value[1:] # Remove leading quote
                        else:
                            processed_record[key] = value
                    restored_list.append(processed_record)
                final_restored_data = {table_name: restored_list}

            # Save to YAML file
            file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    yaml.dump(final_restored_data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
                msg = f"Successfully restored {table_name} to {file_path}"
                print(msg)
                if hasattr(st, 'secrets'): st.success(f"Successfully restored {table_name} from Google Sheet '{TABLE_MAP[table_name]}'.")
                return True, msg
            except Exception as write_err:
                msg = f"Error writing restored data to {file_path}: {write_err}"
                print(msg)
                if hasattr(st, 'secrets'): st.error(f"Error writing restored data to local file {file_path}: {write_err}")
                return False, msg

        except gspread.exceptions.APIError as e:
            msg = f"Google Sheets API Error restoring {table_name}: {e}"
            print(msg)
            if hasattr(st, 'secrets'): st.error(msg)
            return False, msg
        except Exception as e:
            msg = f"Error restoring {table_name} from Google Sheets: {e}"
            print(msg)
            if hasattr(st, 'secrets'): st.error(f"An unexpected error occurred while restoring {table_name}: {e}")
            return False, msg

    def restore_all_data(self, tab_name=None): # Added tab_name parameter, though not used here
        """Restore all tables from their dedicated Google Sheets."""
        if not self.spreadsheet:
            print("Not connected. Cannot restore all data.")
            if not self.connect(): return False, "Failed to connect"
            if not self.spreadsheet: return False, "Spreadsheet object missing after connect"

        results = {}
        print(f"Starting restore for all mapped tables...")
        if hasattr(st, 'secrets'): st.info(f"Starting restore for all tables from their dedicated sheets...")
        all_success = True
        error_messages = []
        success_messages = []
        for table_name in TABLE_MAP.keys():
            print(f"--- Restoring {table_name} from sheet '{TABLE_MAP[table_name]}' ---")
            restore_success, msg = self.restore_data(table_name)
            results[table_name] = restore_success
            print(f"--- Finished restoring {table_name} (Success: {restore_success}) ---")
            if restore_success:
                success_messages.append(f"{table_name}: {msg}")
            else:
                all_success = False
                error_messages.append(f"{table_name}: {msg}")
                if hasattr(st, 'secrets'): st.warning(f"Restore failed for table: {table_name}")

        print("Finished restoring all tables.")
        final_message = ""
        if all_success:
            final_message = f"Finished restoring all tables successfully. Details: {'; '.join(success_messages)}"
            if hasattr(st, 'secrets'): st.success(final_message)
        else:
            final_message = f"Finished restoring all tables, but some tables failed: {'; '.join(error_messages)}"
            if hasattr(st, 'secrets'): st.error(final_message)
        return all_success, final_message

# --- Singleton Instance and Helper Functions ---

_instance = None

def get_sync_instance():
    """Get the singleton instance of GoogleSheetsSync."""
    global _instance
    if _instance is None:
        print("Initializing GoogleSheetsSync instance...")
        try:
            _instance = GoogleSheetsSync()
            if not _instance.client or not _instance.spreadsheet:
                print("Failed to establish connection during initial instance creation.")
                _instance = None
        except Exception as e:
            print(f"Failed to initialize GoogleSheetsSync instance: {e}")
            if hasattr(st, 'secrets'):
                st.error(f"Failed to initialize Google Sheets connection: {e}")
            _instance = None
    elif _instance and (not _instance.client or not _instance.spreadsheet):
        print("Re-attempting connection for existing instance...")
        if not _instance.connect():
            print("Failed to re-establish connection.")

    return _instance

def sync_on_data_change(table_name):
    """Sync a specific table when data changes."""
    # This function now syncs the *entire* current state of the YAML 
    # to the corresponding sheet using the logic in sync_data 
    # (overwrite for config, append for others).
    print(f"Sync triggered for table: {table_name}")
    sync = get_sync_instance()
    if sync:
        success, msg = sync.sync_data(table_name)
        if success:
            print(f"Sync completed for {table_name}: {msg}")
            # if hasattr(st, 'secrets'): st.toast(f"Data for {table_name} synced to Google Sheets.")
        else:
            print(f"Sync failed for {table_name}: {msg}")
            if hasattr(st, 'secrets'):
                st.error(f"Failed to sync data for {table_name} to Google Sheets: {msg}")
        return success
    else:
        print("Sync instance not available. Cannot sync.")
        if hasattr(st, 'secrets'):
            st.error("Google Sheets connection not available. Cannot sync data.")
        return False

def sync_all():
    """Sync all tables."""
    sync = get_sync_instance()
    if sync:
        return sync.sync_all_data()
    else:
        print("Sync instance not available. Cannot sync all.")
        if hasattr(st, 'secrets'):
            st.error("Google Sheets connection not available. Cannot sync all data.")
        # Return False and an error message for consistency
        return False, "Google Sheets connection not available."

def restore_table(table_name):
    """Restore a specific table from Google Sheets."""
    sync = get_sync_instance()
    if sync:
        return sync.restore_data(table_name)
    else:
        print("Sync instance not available. Cannot restore table.")
        if hasattr(st, 'secrets'):
            st.error("Google Sheets connection not available. Cannot restore table.")
        return False, "Google Sheets connection not available."

def restore_all(tab_name=None):
    """Restore all tables from Google Sheets."""
    sync = get_sync_instance()
    if sync:
        return sync.restore_all_data(tab_name=tab_name) # Pass tab_name
    else:
        print("Sync instance not available. Cannot restore all.")
        if hasattr(st, 'secrets'):
            st.error("Google Sheets connection not available. Cannot restore all data.")
        return False, "Google Sheets connection not available."

# Test block (for local execution, won't use Streamlit secrets)
if __name__ == "__main__":
    print("Running Google Sheets Sync Test (local mode, adapted for template)...")
    # Ensure data directory exists for local testing
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created data directory: {DATA_DIR}")
        # Optionally create dummy YAML files if needed for testing
        # with open(os.path.join(DATA_DIR, 'marketing_activities.yaml'), 'w') as f: yaml.dump({'marketing_activities': []}, f)
        # with open(os.path.join(DATA_DIR, 'config.yaml'), 'w') as f: yaml.dump({'Key': 'app_name', 'Value': 'Test App'}, f)

    sync = GoogleSheetsSync()
    if sync.client and sync.spreadsheet:
        print("Connection successful!")
        # Test getting current month tab name
        print(f"Current month tab name: {sync.get_current_month_tab_name()}")

        # Test syncing one table (e.g., activities)
        print("\nTesting sync_data for marketing_activities...")
        # Ensure you have some data in data/marketing_activities.yaml for testing
        sync_success, sync_msg = sync.sync_data("marketing_activities")
        print(f"Sync result for marketing_activities: {sync_success} - {sync_msg}")

        # Test restoring one table
        # print("\nTesting restore_data for marketing_activities...")
        # restore_success, restore_msg = sync.restore_data("marketing_activities")
        # print(f"Restore result for marketing_activities: {restore_success} - {restore_msg}")
    else:
        print("Connection failed! Check local credentials file and API access.")

