"""
Google Sheets Sync Module for AI Marketing Tracker (Adapted for Specific Template)

This module handles synchronization between the local application data and Google Sheets,
assuming dedicated sheets (
    'Activities', 'Followups', 'Users', 'Config') exist
as per the provided template.
Includes incremental sync logic to avoid duplicates.
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
from utils_with_edit_delete import get_app_config, update_app_config # For last sync time

# Constants
# Use the user-provided ID
SPREADSHEET_ID = "1IRZ6iLmE62lPyiv8sJqLMQBH66fci7L-H9NuGiscMvo"
CREDENTIALS_FILE = "service_account_key.json"
DATA_DIR = "data"
WIB_TZ = pytz.timezone("Asia/Bangkok") # Define WIB timezone (UTC+7)
LAST_MANUAL_SYNC_KEY = "last_manual_sync_timestamp_wib"

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

# --- Helper to get last sync time --- 
def get_last_manual_sync_time():
    config = get_app_config()
    return config.get(LAST_MANUAL_SYNC_KEY)

# --- Helper to set last sync time --- 
def set_last_manual_sync_time():
    timestamp_str = datetime.now(WIB_TZ).strftime("%Y-%m-%d %H:%M:%S")
    update_app_config({LAST_MANUAL_SYNC_KEY: timestamp_str})
    print(f"Updated last manual sync time to: {timestamp_str}")

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
                # print("Existing connection seems valid.") # Reduce noise
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
            # else:
                # print("All required sheets found.") # Reduce noise
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
            # print(f"Accessed worksheet: '{target_sheet_name}'") # Reduce noise
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

    def sync_data(self, table_name, incremental=False):
        """Sync data from a specific table's YAML file to its dedicated Google Sheet.
        
        Args:
            table_name (str): The internal name of the table to sync.
            incremental (bool): If True, only append new records based on ID.
                                If False (default), overwrite the sheet (used for config).
        """
        print(f"Starting sync for table: {table_name} (Incremental: {incremental})")
        worksheet = self._get_target_sheet(table_name)
        if not worksheet:
            return False, f"Target sheet for {table_name} not found."

        file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
        if not os.path.exists(file_path):
            print(
                f"Data file not found: {file_path}, skipping sync for {table_name}."
            )
            return False, f"Data file {file_path} not found."

        # Read data from YAML
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
                    return False, "Invalid config.yaml format."
            elif isinstance(raw_data, dict) and table_name in raw_data:
                data_to_sync = raw_data[table_name]
                if not isinstance(data_to_sync, list):
                    print(
                        f"Warning: Expected list under key '{table_name}' in {file_path}, found {type(data_to_sync)}."
                    )
                    data_to_sync = []
            elif isinstance(raw_data, list):
                print(
                    f"Warning: Reading direct list from {file_path}. Expected dict with key '{table_name}'."
                )
                data_to_sync = raw_data
            else:
                print(
                    f"Warning: Unexpected YAML structure in {file_path}. Cannot sync."
                )
                return False, f"Unexpected YAML structure in {file_path}."

        except Exception as e:
            print(f"Error reading or parsing YAML file {file_path}: {e}")
            if hasattr(st, 'secrets'):
                st.error(f"Error reading data file for {table_name}: {e}")
            return False, f"Error reading YAML file {file_path}."

        # Get the expected headers
        expected_headers = EXPECTED_HEADERS.get(table_name)
        if not expected_headers:
            print(f"Error: No expected headers defined for table '{table_name}'.")
            if hasattr(st, 'secrets'):
                st.error(f"Configuration error: Headers missing for {table_name}."
                         )
            return False, f"Headers missing for {table_name}."

        # --- Sync Logic --- 
        try:
            if table_name == 'config':
                # Config: Always overwrite
                print(
                    f"Syncing config data (overwrite) to sheet '{TABLE_MAP[table_name]}'."
                )
                values_to_update = [expected_headers]  # Start with header row
                for key, value in config_data_dict.items():
                    values_to_update.append([str(key), str(value)])

                worksheet.clear()
                worksheet.update(f'A1:B{len(values_to_update)}',
                                 values_to_update,
                                 value_input_option='USER_ENTERED') 
                msg = f"Successfully synced {len(values_to_update)-1} config items (overwrite)."
                print(msg)
                return True, msg

            else:
                # Activities, Followups, Users: Overwrite or Incremental Append
                if not data_to_sync:
                    msg = f"No data entries found in {file_path} for {table_name}. Nothing to sync."
                    print(msg)
                    # If overwriting, clear the sheet
                    if not incremental:
                         print(f"Clearing sheet '{TABLE_MAP[table_name]}' as part of overwrite sync.")
                         worksheet.clear()
                         worksheet.update('A1', [expected_headers], value_input_option='USER_ENTERED')
                    return True, msg

                # Prepare data rows from YAML
                yaml_rows = []
                yaml_ids = set()
                id_column_index = expected_headers.index('id') if 'id' in expected_headers else -1

                for item in data_to_sync:
                    if not isinstance(item, dict):
                        print(
                            f"Warning: Skipping non-dict item in {table_name} data: {item}"
                        )
                        continue

                    # Ensure ID exists (especially for users)
                    if id_column_index != -1 and 'id' not in item:
                        if table_name == 'users':
                            item['id'] = f"usr-{uuid.uuid4().hex[:8]}"
                            print(
                                f"Generated missing ID for user: {item.get('username', 'N/A')} -> {item['id']}"
                            )
                        else:
                             print(f"Warning: Skipping item in {table_name} due to missing ID: {item}")
                             continue # Skip items without ID if ID is expected
                    
                    item_id = item.get('id') if id_column_index != -1 else None
                    if item_id:
                        yaml_ids.add(item_id)

                    row_values = []
                    for header in expected_headers:
                        value = item.get(header, "")
                        formatted_value = self._format_value(value, header, table_name)
                        row_values.append(formatted_value)
                    yaml_rows.append(row_values)

                if not yaml_rows:
                    msg = f"No valid data rows prepared from YAML for {table_name}. Nothing to sync."
                    print(msg)
                    # If overwriting, clear the sheet
                    if not incremental:
                         print(f"Clearing sheet '{TABLE_MAP[table_name]}' as part of overwrite sync.")
                         worksheet.clear()
                         worksheet.update('A1', [expected_headers], value_input_option='USER_ENTERED')
                    return True, msg

                # --- Apply Sync Strategy --- 
                if incremental and id_column_index != -1:
                    # Incremental Append: Get existing IDs from sheet
                    print(f"Performing incremental sync for {table_name}. Fetching existing IDs...")
                    try:
                        # Get only the ID column (assuming it's the first column, index 1)
                        # Adjust col_index if 'id' is not the first column
                        id_col_letter = gspread.utils.rowcol_to_a1(1, id_column_index + 1).rstrip('1')
                        existing_ids_raw = worksheet.col_values(id_column_index + 1)
                        # Skip header row and remove potential leading quotes from formatted IDs
                        existing_ids = {str(id_val).lstrip("'") for id_val in existing_ids_raw[1:] if id_val}
                        print(f"Found {len(existing_ids)} existing IDs in sheet '{TABLE_MAP[table_name]}'.")
                    except Exception as e:
                        msg = f"Error fetching existing IDs from sheet '{TABLE_MAP[table_name]}': {e}. Cannot perform incremental sync."
                        print(msg)
                        if hasattr(st, 'secrets'): st.error(msg)
                        return False, msg

                    # Filter YAML rows to find new ones
                    rows_to_append = []
                    for row in yaml_rows:
                        row_id = str(row[id_column_index]).lstrip("'") # Get ID from formatted row
                        if row_id not in existing_ids:
                            rows_to_append.append(row)
                    
                    if not rows_to_append:
                        msg = f"No new records found in YAML for {table_name} to append incrementally."
                        print(msg)
                        return True, msg
                    
                    # Append only the new rows
                    print(
                        f"Appending {len(rows_to_append)} new rows incrementally to sheet '{TABLE_MAP[table_name]}'."
                    )
                    worksheet.append_rows(rows_to_append,
                                          value_input_option='USER_ENTERED',
                                          insert_data_option='INSERT_ROWS',
                                          table_range='A1')
                    msg = f"Successfully appended {len(rows_to_append)} new rows for {table_name} incrementally."
                    print(msg)
                    return True, msg

                else:
                    # Overwrite Sync
                    print(
                        f"Performing overwrite sync for {table_name} with {len(yaml_rows)} rows."
                    )
                    worksheet.clear()
                    # Prepare data including headers
                    data_to_write = [expected_headers] + yaml_rows
                    # Determine range dynamically
                    end_cell = gspread.utils.rowcol_to_a1(len(data_to_write), len(expected_headers))
                    worksheet.update(f'A1:{end_cell}',
                                     data_to_write,
                                     value_input_option='USER_ENTERED')
                    msg = f"Successfully synced {len(yaml_rows)} rows for {table_name} (overwrite)."
                    print(msg)
                    return True, msg

        except gspread.exceptions.APIError as e:
            msg = f"Google Sheets API Error syncing {table_name}: {e}"
            print(msg)
            if hasattr(st, 'secrets'):
                st.error(msg)
            return False, msg
        except Exception as e:
            msg = f"Unexpected error during sync for {table_name}: {e}"
            print(msg)
            if hasattr(st, 'secrets'):
                st.error(
                    f"An unexpected error occurred while syncing {table_name}: {e}"
                )
            return False, msg

    def sync_all_data(self, incremental=False):
        """Sync all tables based on the TABLE_MAP.
        
        Args:
            incremental (bool): If True, use incremental append for Activities, Followups, Users.
                                Config is always overwritten.
        """
        if not self.spreadsheet:
            print("Not connected. Cannot sync all data.")
            if not self.connect(): return False, "Failed to connect"
            if not self.spreadsheet: return False, "Spreadsheet object missing after connect"

        results = {}
        print(f"Starting sync for all mapped tables... (Incremental: {incremental})")
        if hasattr(st, 'secrets'): st.info(f"Starting sync for all tables... (Incremental: {incremental})")
        all_success = True
        error_messages = []
        success_messages = []
        for table_name in TABLE_MAP.keys():
            print(f"--- Syncing {table_name} to sheet '{TABLE_MAP[table_name]}' ---")
            # Determine sync type for this table
            is_incremental = incremental and table_name != 'config'
            sync_success, msg = self.sync_data(table_name, incremental=is_incremental)
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
            # Update last sync time only if all tables succeeded
            set_last_manual_sync_time()
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
                restored_list = []
                expected_keys = EXPECTED_HEADERS.get(table_name, [])
                for record in sheet_data:
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

    def get_available_tabs(self):
        """Get a list of all worksheet names in the spreadsheet."""
        if not self.spreadsheet:
            print("Not connected. Cannot get available tabs.")
            if not self.connect(): return False, "Failed to connect", []
            if not self.spreadsheet: return False, "Spreadsheet object missing after connect", []
        try:
            tabs = [sheet.title for sheet in self.spreadsheet.worksheets()]
            return True, "Successfully retrieved tabs", tabs
        except Exception as e:
            msg = f"Error getting available tabs: {e}"
            print(msg)
            if hasattr(st, 'secrets'): st.error(msg)
            return False, msg, []

# --- Singleton Instance --- 
_sync_instance = None

def get_sync_instance():
    """Get the singleton instance of GoogleSheetsSync."""
    global _sync_instance
    if _sync_instance is None:
        print("Creating new GoogleSheetsSync instance...")
        _sync_instance = GoogleSheetsSync()
    # Always try to ensure connection is active
    elif not _sync_instance.connect():
        print("Failed to ensure connection for existing instance.")
        # Optionally, try recreating the instance if connection fails persistently
        # _sync_instance = GoogleSheetsSync()
    return _sync_instance
