"""
Google Sheets Sync Module for AI Marketing Tracker

This module handles synchronization between the local application data and Google Sheets.
It provides functionality for:
1. Real-time sync on data changes
2. Monthly tab creation and management
3. Data restoration from Google Sheets
"""

import os
import gspread
import yaml
import pandas as pd
from datetime import datetime
import streamlit as st # Import Streamlit

# Constants
SPREADSHEET_ID = "1SdEX5TzMzKfKcE1oCuaez2ctxgIxwwipkk9NT0jOYtI"
CREDENTIALS_FILE = "service_account_key.json"
DATA_DIR = "data"
TABLES = ["marketing_activities", "followups", "users", "config"]

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
        try:
            # Try to authenticate using Streamlit Secrets first (for deployment)
            if hasattr(st, 'secrets') and "google_credentials" in st.secrets:
                print("Authenticating using Streamlit Secrets...")
                creds_dict = dict(st.secrets["google_credentials"])
                self.client = gspread.service_account_from_dict(creds_dict)
                print("Successfully authenticated using Streamlit Secrets.")
            # Fallback to local credentials file (for local development)
            elif os.path.exists(self.credentials_file):
                print(f"Authenticating using local file: {self.credentials_file}...")
                self.client = gspread.service_account(filename=self.credentials_file)
                print("Successfully authenticated using local file.")
            else:
                print("Error: Google credentials not found in Streamlit Secrets or local file.")
                st.error("Google Sheets credentials configuration missing. Please configure Streamlit Secrets or provide service_account_key.json.")
                return False

            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            print(f"Successfully connected to Google Sheets: {self.spreadsheet.title}")
            return True
            
        except gspread.exceptions.APIError as e:
            print(f"Google Sheets API Error: {e}")
            st.error(f"Google Sheets API Error: {e}. Check permissions or API enablement.")
            if "PERMISSION_DENIED" in str(e):
                print("Ensure the service account email has editor access to the Google Sheet.")
                st.warning("Ensure the service account email has editor access to the Google Sheet.")
            elif "SERVICE_USAGE" in str(e):
                print("Ensure the Google Sheets API is enabled in your Google Cloud project.")
                st.warning("Ensure the Google Sheets API is enabled in your Google Cloud project.")
            return False
        except FileNotFoundError:
            # This case is handled by the initial check, but kept for robustness
            print(f"Error: Credentials file not found at {self.credentials_file} (when not using Secrets).")
            st.error(f"Credentials file not found at {self.credentials_file}. Ensure it exists for local development if not using Secrets.")
            return False
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            st.error(f"An unexpected error occurred while connecting to Google Sheets: {e}")
            return False
    
    def get_current_month_tab_name(self):
        """Get the tab name for the current month."""
        now = datetime.now()
        return f"{now.strftime("%Y_%m")}"
    
    def ensure_monthly_tab_exists(self):
        """Ensure that a tab exists for the current month."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot ensure tab exists.")
            # Attempt to reconnect if needed?
            if not self.connect():
                 st.error("Failed to connect to Google Sheets. Cannot ensure monthly tab exists.")
                 return None
            # If connect succeeds, self.spreadsheet should be set
            if not self.spreadsheet:
                 st.error("Connection established, but spreadsheet object is still missing.")
                 return None

        tab_name = self.get_current_month_tab_name()
        
        # Check if the tab already exists
        try:
            self.spreadsheet.worksheet(tab_name)
            print(f"Tab {tab_name} already exists.")
            return tab_name
        except gspread.exceptions.WorksheetNotFound:
            # Create a new tab for the current month
            print(f"Creating new tab for {tab_name}")
            try:
                worksheet = self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=26)
                # Initialize the tab with headers for each table
                self._initialize_monthly_tab(tab_name)
                return tab_name
            except Exception as e:
                print(f"Error creating worksheet {tab_name}: {e}")
                st.error(f"Error creating worksheet {tab_name}: {e}")
                return None
        except Exception as e:
            print(f"Error checking for worksheet {tab_name}: {e}")
            st.error(f"Error checking for worksheet {tab_name}: {e}")
            return None

    def _initialize_monthly_tab(self, tab_name):
        """Initialize a new monthly tab with headers for each table."""
        try:
            worksheet = self.spreadsheet.worksheet(tab_name)
            
            # Clear any existing data
            worksheet.clear()
            
            # Add headers and section separators for each table
            row = 1
            for table in TABLES:
                # Add table name as a header
                worksheet.update_cell(row, 1, f"=== {table.upper()} ===")
                row += 1
                
                # Get headers for this table
                headers = self._get_table_headers(table)
                if headers:
                    # Update header row
                    header_range = f"A{row}:{chr(64 + len(headers))}{row}"
                    worksheet.update(header_range, [headers])
                    row += 1
                
                # Add empty rows for data + separator
                row += 21 # Space for 20 data rows + 1 empty separator row
        except Exception as e:
            print(f"Error initializing tab {tab_name}: {e}")
            st.error(f"Error initializing tab {tab_name}: {e}")

    def _get_table_headers(self, table):
        """Get the headers for a specific table from its YAML structure."""
        try:
            file_path = os.path.join(DATA_DIR, f"{table}.yaml")
            if not os.path.exists(file_path):
                return []
                
            with open(file_path, 'r') as file:
                # Read the raw structure first
                raw_data = yaml.safe_load(file)
            
            if raw_data is None: # Handle empty YAML file
                return []

            # Extract the actual data list/dict based on structure
            data_list = []
            if isinstance(raw_data, dict) and table in raw_data:
                data_list = raw_data[table]
            elif isinstance(raw_data, list):
                 data_list = raw_data
            elif isinstance(raw_data, dict) and table == 'config': # Config is special case
                 return ["Key", "Value"]
            else:
                 # If structure is unexpected or data_list is not a list of dicts
                 return []

            # Determine headers from the list of dictionaries
            if isinstance(data_list, list) and len(data_list) > 0 and all(isinstance(item, dict) for item in data_list):
                all_keys = set()
                for item in data_list:
                    all_keys.update(item.keys())
                return sorted(list(all_keys)) # Return sorted list for consistency
            elif isinstance(data_list, list) and len(data_list) == 0: # Handle empty list under key
                 # Try to get headers from a template or default structure if available
                 # For now, return empty
                 return []
            return [] # Default empty if structure is unexpected
        except Exception as e:
            print(f"Error getting headers for {table}: {e}")
            return []

    def sync_data(self, table_name, force_sync=False):
        """Sync data from a specific table to Google Sheets."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot sync data.")
            # Attempt to reconnect
            if not self.connect():
                 st.error("Failed to connect to Google Sheets. Cannot sync data.")
                 return False
            if not self.spreadsheet:
                 st.error("Connection established, but spreadsheet object is still missing.")
                 return False
            
        try:
            tab_name = self.ensure_monthly_tab_exists()
            if not tab_name:
                print(f"Failed to ensure monthly tab exists. Cannot sync {table_name}.")
                st.error(f"Failed to ensure monthly tab exists. Cannot sync {table_name}.")
                return False
            worksheet = self.spreadsheet.worksheet(tab_name)
            
            file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
                
            # Read data considering the root key structure
            data = []
            with open(file_path, 'r') as file:
                raw_data = yaml.safe_load(file)
                if raw_data is None: # Handle empty file
                    data = [] if table_name != 'config' else {}
                elif isinstance(raw_data, dict) and table_name in raw_data:
                    data = raw_data[table_name]
                elif isinstance(raw_data, list):
                    data = raw_data
                elif isinstance(raw_data, dict) and table_name == 'config':
                    data = raw_data
                else:
                    print(f"Warning: Unexpected YAML structure in {file_path}. Expected list or dict with key '{table_name}'.")
                    data = [] # Default to empty list

            # Find the section header in the worksheet
            try:
                cell_list = worksheet.findall(f"=== {table_name.upper()} ===")
            except Exception as find_err:
                 print(f"Error finding section header for {table_name} in worksheet {tab_name}: {find_err}")
                 st.error(f"Error finding section header for {table_name} in worksheet {tab_name}: {find_err}")
                 return False
                 
            if not cell_list:
                print(f"Section for {table_name} not found in worksheet {tab_name}. Attempting to re-initialize tab.")
                st.warning(f"Section header for {table_name} not found in worksheet {tab_name}. Re-initializing tab structure.")
                self._initialize_monthly_tab(tab_name) # Re-initialize headers
                # Try finding again
                try:
                    cell_list = worksheet.findall(f"=== {table_name.upper()} ===")
                    if not cell_list:
                         print(f"Section for {table_name} still not found after re-initialization.")
                         st.error(f"Section header for {table_name} could not be created/found in worksheet {tab_name}. Sync failed.")
                         return False
                except Exception as find_err_2:
                     print(f"Error finding section header after re-init for {table_name}: {find_err_2}")
                     st.error(f"Error finding section header after re-init for {table_name}: {find_err_2}")
                     return False

            header_row_num = cell_list[0].row + 1
            data_start_row = header_row_num + 1
            
            # Get headers from the sheet (or generate if needed)
            headers = self._get_table_headers(table_name)
            if not headers:
                 print(f"Could not determine headers for {table_name}. Skipping sync.")
                 # Optionally try reading headers from sheet as fallback?
                 # headers = worksheet.row_values(header_row_num)
                 # if not headers:
                 #    st.error(f"Could not determine headers for {table_name}. Sync failed.")
                 #    return False
                 st.error(f"Could not determine headers for {table_name} from YAML. Sync failed.")
                 return False

            # Convert data to list of lists for batch update
            values_to_update = [headers] # Start with header row
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                for item in data:
                    # Ensure row values match the order of headers
                    row_values = [item.get(header, "") for header in headers]
                    values_to_update.append(row_values)
            elif isinstance(data, dict) and table_name == 'config':
                # Config needs special handling (Key, Value)
                if headers == ["Key", "Value"]:
                     for key, value in data.items():
                         values_to_update.append([key, str(value)]) # Ensure value is string
                else:
                     print(f"Header mismatch for config table. Expected [Key, Value], got {headers}")
                     st.warning(f"Header mismatch for config table. Skipping sync.")
                     # Don't sync if headers don't match expected config format
                     values_to_update = [headers] # Send only headers
            elif isinstance(data, list) and len(data) == 0:
                 print(f"No data entries found in {file_path} for {table_name}.")
                 # values_to_update remains just [headers]
            else:
                print(f"Unsupported data format or empty data for {table_name}.")
                st.warning(f"Data format issue or empty data for {table_name}. Syncing headers only.")
                # values_to_update remains just [headers]

            # Determine range to clear and update
            clear_start_row = data_start_row
            # Calculate a reasonable end row to clear, e.g., current data rows + buffer
            clear_end_row = clear_start_row + max(50, len(values_to_update) + 10) 
            clear_start_col_char = 'A'
            clear_end_col_char = chr(64 + len(headers)) if headers else 'Z'
            clear_range = f"{clear_start_col_char}{clear_start_row}:{clear_end_col_char}{clear_end_row}"
            
            try:
                print(f"Clearing range {clear_range} for {table_name} in tab {tab_name}")
                worksheet.batch_clear([clear_range])
            except Exception as clear_err:
                 print(f"Error clearing range {clear_range} for {table_name}: {clear_err}")
                 st.error(f"Error clearing sheet range for {table_name}: {clear_err}")
                 # Decide if we should proceed or return False
                 return False # Safer to stop if clearing fails

            # Update with new data (including headers)
            if values_to_update:
                update_start_row = header_row_num # Start update from header row
                update_end_row = update_start_row + len(values_to_update) - 1
                update_start_col_char = 'A'
                update_end_col_char = chr(64 + len(headers))
                update_range = f"{update_start_col_char}{update_start_row}:{update_end_col_char}{update_end_row}"
                
                try:
                    print(f"Updating range {update_range} for {table_name} with {len(values_to_update)} rows (incl. header)")
                    worksheet.update(update_range, values_to_update, value_input_option='USER_ENTERED')
                    print(f"Successfully synced {len(values_to_update)-1} data rows for {table_name} to Google Sheets tab {tab_name}")
                except Exception as update_err:
                     print(f"Error updating range {update_range} for {table_name}: {update_err}")
                     st.error(f"Error writing data to Google Sheets for {table_name}: {update_err}")
                     return False # Sync failed if update fails
            else:
                 # This case should ideally not happen if headers are always present
                 print(f"No values (including headers) to update for {table_name}.")
                 st.warning(f"No data or headers prepared for {table_name}. Nothing synced.")

            return True # Sync completed (or attempted fully)
            
        except gspread.exceptions.APIError as e:
             print(f"Google Sheets API Error syncing {table_name}: {e}")
             st.error(f"Google Sheets API Error syncing {table_name}: {e}")
             return False
        except Exception as e:
            print(f"Error syncing {table_name} to Google Sheets: {e}")
            st.error(f"An unexpected error occurred while syncing {table_name}: {e}")
            return False
    
    def sync_all_data(self, force_sync=False):
        """Sync all tables to Google Sheets."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot sync all data.")
            if not self.connect():
                 st.error("Failed to connect to Google Sheets. Cannot sync all data.")
                 return False
            if not self.spreadsheet:
                 st.error("Connection established, but spreadsheet object is still missing.")
                 return False
            
        results = {}
        print("Starting sync for all tables...")
        st.info("Starting sync for all tables...")
        all_success = True
        for table in TABLES:
            print(f"--- Syncing {table} ---")
            results[table] = self.sync_data(table, force_sync)
            print(f"--- Finished syncing {table} (Success: {results[table]}) ---")
            if not results[table]:
                 all_success = False
                 st.warning(f"Sync failed for table: {table}")
        print("Finished syncing all tables.")
        if all_success:
             st.success("Finished syncing all tables successfully.")
        else:
             st.error("Finished syncing all tables, but some tables failed.")
        return results
    
    def restore_data(self, table_name, tab_name=None):
        """Restore data from Google Sheets to local YAML file."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot restore data.")
            if not self.connect():
                 st.error("Failed to connect to Google Sheets. Cannot restore data.")
                 return False
            if not self.spreadsheet:
                 st.error("Connection established, but spreadsheet object is still missing.")
                 return False
            
        try:
            if not tab_name:
                tab_name = self.get_current_month_tab_name()
            
            try:
                worksheet = self.spreadsheet.worksheet(tab_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"Tab {tab_name} not found. Cannot restore {table_name}.")
                st.warning(f"Worksheet tab '{tab_name}' not found. Cannot restore {table_name}.")
                return False
            
            # Find the section header
            try:
                cell_list = worksheet.findall(f"=== {table_name.upper()} ===")
            except Exception as find_err:
                 print(f"Error finding section header for {table_name} in worksheet {tab_name}: {find_err}")
                 st.error(f"Error finding section header for {table_name} in worksheet {tab_name}: {find_err}")
                 return False
                 
            if not cell_list:
                print(f"Section for {table_name} not found in worksheet {tab_name}")
                st.warning(f"Section header for {table_name} not found in worksheet {tab_name}. Cannot restore.")
                return False
            
            header_row_num = cell_list[0].row + 1
            data_start_row = header_row_num + 1
            
            # Get headers from the sheet
            try:
                headers = worksheet.row_values(header_row_num)
            except Exception as header_err:
                 print(f"Error reading header row {header_row_num} for {table_name}: {header_err}")
                 st.error(f"Error reading header row for {table_name}: {header_err}")
                 return False
                 
            if not headers:
                print(f"No headers found for {table_name} in row {header_row_num}")
                st.warning(f"No headers found for {table_name} in worksheet {tab_name}. Cannot restore.")
                return False
            
            # Fetch all data below the header in the section
            # Estimate data range (e.g., 50 rows max per section for restore)
            data_end_row = data_start_row + 49
            range_to_fetch = f"A{data_start_row}:{chr(64 + len(headers))}{data_end_row}"
            try:
                sheet_data = worksheet.get(range_to_fetch, value_render_option='FORMATTED_VALUE')
            except Exception as fetch_err:
                 print(f"Error fetching data range {range_to_fetch} for {table_name}: {fetch_err}")
                 st.error(f"Error fetching data from Google Sheets for {table_name}: {fetch_err}")
                 return False

            # Process fetched data into YAML structure
            restored_data_list = []
            if table_name == "config":
                restored_data_dict = {}
                for row in sheet_data:
                    if len(row) >= 2 and row[0]: # Check if key exists
                        restored_data_dict[row[0]] = row[1]
                # Structure for config.yaml might be nested, adjust as needed
                # Assuming flat Key: Value for now based on sync logic
                final_restored_data = restored_data_dict 
            else:
                restored_data_list = []
                for row in sheet_data:
                    if not any(val for val in row if val): # Skip entirely empty rows more reliably
                        continue
                    item = {}
                    for i, header in enumerate(headers):
                        item[header] = row[i] if i < len(row) else ""
                    # Only add if item is not effectively empty
                    if any(val for val in item.values() if val):
                        restored_data_list.append(item)
                # Structure for other YAMLs is { 'table_name': [...] }
                final_restored_data = {table_name: restored_data_list}
            
            # Save to YAML file
            file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
            try:
                with open(file_path, 'w') as file:
                    # Use sort_keys=False to maintain order if important
                    yaml.dump(final_restored_data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
                print(f"Successfully restored {table_name} from Google Sheets tab {tab_name} to {file_path}")
                st.success(f"Successfully restored {table_name} from Google Sheets tab {tab_name}.")
                return True
            except Exception as write_err:
                 print(f"Error writing restored data to {file_path}: {write_err}")
                 st.error(f"Error writing restored data to local file {file_path}: {write_err}")
                 return False

        except gspread.exceptions.APIError as e:
             print(f"Google Sheets API Error restoring {table_name}: {e}")
             st.error(f"Google Sheets API Error restoring {table_name}: {e}")
             return False
        except Exception as e:
            print(f"Error restoring {table_name} from Google Sheets: {e}")
            st.error(f"An unexpected error occurred while restoring {table_name}: {e}")
            return False
    
    def restore_all_data(self, tab_name=None):
        """Restore all tables from Google Sheets."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot restore all data.")
            if not self.connect():
                 st.error("Failed to connect to Google Sheets. Cannot restore all data.")
                 return False
            if not self.spreadsheet:
                 st.error("Connection established, but spreadsheet object is still missing.")
                 return False
            
        results = {}
        effective_tab_name = tab_name or self.get_current_month_tab_name()
        print(f"Starting restore for all tables from tab: {effective_tab_name}...")
        st.info(f"Starting restore for all tables from tab: {effective_tab_name}...")
        all_success = True
        for table in TABLES:
            print(f"--- Restoring {table} ---")
            results[table] = self.restore_data(table, effective_tab_name)
            print(f"--- Finished restoring {table} (Success: {results[table]}) ---")
            if not results[table]:
                 all_success = False
                 st.warning(f"Restore failed for table: {table}")
        print("Finished restoring all tables.")
        if all_success:
             st.success("Finished restoring all tables successfully.")
        else:
             st.error("Finished restoring all tables, but some tables failed.")
        return results

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
                 # Don't set _instance if connection failed
                 _instance = None 
        except Exception as e:
            print(f"Failed to initialize GoogleSheetsSync instance: {e}")
            st.error(f"Failed to initialize Google Sheets connection: {e}")
            _instance = None # Ensure it stays None if init fails
    # Check connection status if instance exists but might be disconnected
    elif _instance and (not _instance.client or not _instance.spreadsheet):
         print("Re-attempting connection for existing instance...")
         if not _instance.connect():
              print("Failed to re-establish connection.")
              # Consider if instance should be invalidated
              # _instance = None 
         
    return _instance

def sync_on_data_change(table_name):
    """Sync a specific table when data changes."""
    print(f"Sync triggered for table: {table_name}")
    sync = get_sync_instance()
    if sync:
        success = sync.sync_data(table_name)
        if success:
             print(f"Sync successful for {table_name}.")
             # st.toast(f"Data for {table_name} synced to Google Sheets.") # Optional user feedback
        else:
             print(f"Sync failed for {table_name}.")
             st.error(f"Failed to sync data for {table_name} to Google Sheets.")
        return success
    else:
        print("Sync instance not available. Cannot sync.")
        st.error("Google Sheets connection not available. Cannot sync data.")
        return False

def sync_all():
    """Sync all tables."""
    sync = get_sync_instance()
    if sync:
        return sync.sync_all_data()
    else:
        print("Sync instance not available. Cannot sync all.")
        st.error("Google Sheets connection not available. Cannot sync all data.")
        return False

def restore_table(table_name, tab_name=None):
    """Restore a specific table from Google Sheets."""
    sync = get_sync_instance()
    if sync:
        return sync.restore_data(table_name, tab_name)
    else:
        print("Sync instance not available. Cannot restore table.")
        st.error("Google Sheets connection not available. Cannot restore table.")
        return False

def restore_all(tab_name=None):
    """Restore all tables from Google Sheets."""
    sync = get_sync_instance()
    if sync:
        return sync.restore_all_data(tab_name)
    else:
        print("Sync instance not available. Cannot restore all.")
        st.error("Google Sheets connection not available. Cannot restore all data.")
        return False

# Test the connection and basic sync/restore if this script is run directly
if __name__ == "__main__":
    # Note: This test block won't have access to st.secrets
    # It will rely on the local service_account_key.json file
    print("Running Google Sheets Sync Test (local mode)...")
    
    # Check if running in Streamlit context (basic check)
    try:
        st.set_page_config(layout="wide") # Example Streamlit call
        print("Running within Streamlit context (or Streamlit is importable).")
        # Add more Streamlit specific test logic if needed
    except NameError:
        print("Running outside Streamlit context.")
        # Non-Streamlit test logic
        sync = GoogleSheetsSync()
        if sync.client and sync.spreadsheet:
            print("Connection successful!")
            
            # Test ensuring tab exists
            print("\nTesting ensure_monthly_tab_exists...")
            current_tab = sync.ensure_monthly_tab_exists()
            if current_tab:
                print(f"Current month tab '{current_tab}' ensured.")

                # Test syncing all data
                print("\nTesting sync_all_data...")
                sync_results = sync.sync_all_data()
                print(f"Sync results: {sync_results}")

                # Test restoring all data
                # print("\nTesting restore_all_data...")
                # restore_results = sync.restore_all_data()
                # print(f"Restore results: {restore_results}")
            else:
                print("Failed to ensure current month tab exists. Skipping further tests.")
        else:
            print("Connection failed! Check local credentials file and API access.")


