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
# Removed: from oauth2client.service_account import ServiceAccountCredentials

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
        """Connect to Google Sheets API using gspread and google-auth."""
        try:
            # Authenticate using the service account credentials file
            self.client = gspread.service_account(filename=self.credentials_file)
            
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            print(f"Successfully connected to Google Sheets: {self.spreadsheet.title}")
            return True
        except gspread.exceptions.APIError as e:
            print(f"Google Sheets API Error: {e}")
            # Check for common issues like incorrect permissions or API not enabled
            if "PERMISSION_DENIED" in str(e):
                print("Ensure the service account email has editor access to the Google Sheet.")
            elif "SERVICE_USAGE" in str(e):
                print("Ensure the Google Sheets API is enabled in your Google Cloud project.")
            return False
        except FileNotFoundError:
            print(f"Error: Credentials file not found at {self.credentials_file}")
            return False
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            return False
    
    def get_current_month_tab_name(self):
        """Get the tab name for the current month."""
        now = datetime.now()
        return f"{now.strftime('%Y_%m')}"
    
    def ensure_monthly_tab_exists(self):
        """Ensure that a tab exists for the current month."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot ensure tab exists.")
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
                return None
        except Exception as e:
            print(f"Error checking for worksheet {tab_name}: {e}")
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
                    # worksheet.update_cell(row, 1, "ID") # Assuming ID is part of headers
                    # Update header row
                    header_range = f"A{row}:{chr(64 + len(headers))}{row}"
                    worksheet.update(header_range, [headers])
                    row += 1
                
                # Add empty rows for data + separator
                row += 21 # Space for 20 data rows + 1 empty separator row
        except Exception as e:
            print(f"Error initializing tab {tab_name}: {e}")

    def _get_table_headers(self, table):
        """Get the headers for a specific table from its YAML structure."""
        try:
            file_path = os.path.join(DATA_DIR, f"{table}.yaml")
            if not os.path.exists(file_path):
                # Create empty file if it doesn't exist?
                # For now, return empty list
                return []
                
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            
            if data is None: # Handle empty YAML file
                return []

            # Determine headers based on data structure
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                # List of dictionaries (activities, followups, users)
                # Combine keys from all items to ensure all headers are captured
                all_keys = set()
                for item in data:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                return sorted(list(all_keys)) # Return sorted list for consistency
            elif isinstance(data, dict):
                # Dictionary (config)
                return ["Key", "Value"] # Fixed headers for key-value pairs
            return [] # Default empty if structure is unexpected
        except Exception as e:
            print(f"Error getting headers for {table}: {e}")
            return []

    def sync_data(self, table_name, force_sync=False):
        """Sync data from a specific table to Google Sheets."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot sync data.")
            return False
            
        try:
            tab_name = self.ensure_monthly_tab_exists()
            if not tab_name:
                print(f"Failed to ensure monthly tab exists. Cannot sync {table_name}.")
                return False
            worksheet = self.spreadsheet.worksheet(tab_name)
            
            file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
                
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
                if data is None: # Handle empty file
                    data = [] if table_name != 'config' else {}

            cell_list = worksheet.findall(f"=== {table_name.upper()} ===")
            if not cell_list:
                print(f"Section for {table_name} not found in worksheet {tab_name}")
                # Attempt to re-initialize tab if section missing?
                # For now, return False
                return False
            
            header_row = cell_list[0].row + 1
            start_row = header_row + 1
            
            # Get expected headers from worksheet or generate from data
            # sheet_headers = worksheet.row_values(header_row)
            # Use headers derived from data for consistency
            headers = self._get_table_headers(table_name)
            if not headers:
                 print(f"Could not determine headers for {table_name}. Skipping sync.")
                 return False # Or handle differently, e.g., sync raw data?

            # Convert data to list of lists for batch update
            values_to_update = [headers] # Start with header row
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                for item in data:
                    row_values = [item.get(header, "") for header in headers]
                    values_to_update.append(row_values)
            elif isinstance(data, dict) and table_name == 'config':
                for key, value in data.items():
                    values_to_update.append([key, str(value)]) # Ensure value is string
            else:
                print(f"Unsupported data format for {table_name} or empty data.")
                # If data is empty list/dict, we still might want to clear the sheet section
                # values_to_update remains just [headers]

            # Determine range to clear and update
            # Clear slightly larger area to handle shrinking data
            clear_start_row = header_row + 1
            clear_end_row = clear_start_row + 50 # Clear generous space (adjust as needed)
            clear_start_col_char = 'A'
            clear_end_col_char = chr(64 + len(headers)) if headers else 'Z'
            clear_range = f"{clear_start_col_char}{clear_start_row}:{clear_end_col_char}{clear_end_row}"
            worksheet.batch_clear([clear_range])
            print(f"Cleared range {clear_range} for {table_name}")

            # Update with new data (if any)
            if len(values_to_update) > 1: # Check if there's data beyond headers
                update_start_row = header_row # Update headers as well
                update_end_row = update_start_row + len(values_to_update) -1
                update_start_col_char = 'A'
                update_end_col_char = chr(64 + len(headers))
                update_range = f"{update_start_col_char}{update_start_row}:{update_end_col_char}{update_end_row}"
                worksheet.update(update_range, values_to_update, value_input_option='USER_ENTERED')
                print(f"Successfully synced {len(values_to_update)-1} rows for {table_name} to Google Sheets tab {tab_name}")
            else:
                 print(f"No data to sync for {table_name}.")
                 # Update header row even if no data
                 header_range = f"A{header_row}:{chr(64 + len(headers))}{header_row}"
                 worksheet.update(header_range, [headers])
                 print(f"Updated headers for empty table {table_name}")

            return True
        except gspread.exceptions.APIError as e:
             print(f"Google Sheets API Error syncing {table_name}: {e}")
             return False
        except Exception as e:
            print(f"Error syncing {table_name} to Google Sheets: {e}")
            return False
    
    def sync_all_data(self, force_sync=False):
        """Sync all tables to Google Sheets."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot sync all data.")
            return False
            
        results = {}
        print("Starting sync for all tables...")
        for table in TABLES:
            print(f"--- Syncing {table} ---")
            results[table] = self.sync_data(table, force_sync)
            print(f"--- Finished syncing {table} (Success: {results[table]}) ---")
        print("Finished syncing all tables.")
        return results
    
    def restore_data(self, table_name, tab_name=None):
        """Restore data from Google Sheets to local YAML file."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot restore data.")
            return False
            
        try:
            if not tab_name:
                tab_name = self.get_current_month_tab_name()
            
            try:
                worksheet = self.spreadsheet.worksheet(tab_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"Tab {tab_name} not found. Cannot restore {table_name}.")
                return False
            
            cell_list = worksheet.findall(f"=== {table_name.upper()} ===")
            if not cell_list:
                print(f"Section for {table_name} not found in worksheet {tab_name}")
                return False
            
            header_row_num = cell_list[0].row + 1
            data_start_row = header_row_num + 1
            
            headers = worksheet.row_values(header_row_num)
            if not headers:
                print(f"No headers found for {table_name} in row {header_row_num}")
                return False
            
            # Fetch all data below the header in the section
            # Estimate data range (e.g., 20 rows max per section)
            data_end_row = data_start_row + 19
            range_to_fetch = f"A{data_start_row}:{chr(64 + len(headers))}{data_end_row}"
            sheet_data = worksheet.get(range_to_fetch, value_render_option='FORMATTED_VALUE')

            restored_data = []
            if table_name == "config":
                restored_data = {}
                for row in sheet_data:
                    if len(row) >= 2 and row[0]: # Check if key exists
                        restored_data[row[0]] = row[1]
            else:
                restored_data = []
                for row in sheet_data:
                    if not any(row): # Skip entirely empty rows
                        continue
                    item = {}
                    for i, header in enumerate(headers):
                        item[header] = row[i] if i < len(row) else ""
                    # Only add if item is not empty (e.g., has an ID or some value)
                    if any(item.values()): 
                        restored_data.append(item)
            
            # Save to YAML file
            file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
            try:
                with open(file_path, 'w') as file:
                    yaml.dump(restored_data, file, default_flow_style=False, sort_keys=False)
                print(f"Successfully restored {table_name} from Google Sheets tab {tab_name} to {file_path}")
                return True
            except Exception as e:
                 print(f"Error writing restored data to {file_path}: {e}")
                 return False

        except gspread.exceptions.APIError as e:
             print(f"Google Sheets API Error restoring {table_name}: {e}")
             return False
        except Exception as e:
            print(f"Error restoring {table_name} from Google Sheets: {e}")
            return False
    
    def restore_all_data(self, tab_name=None):
        """Restore all tables from Google Sheets."""
        if not self.spreadsheet:
            print("Not connected to Google Sheets. Cannot restore all data.")
            return False
            
        results = {}
        print(f"Starting restore for all tables from tab: {tab_name or self.get_current_month_tab_name()}...")
        for table in TABLES:
            print(f"--- Restoring {table} ---")
            results[table] = self.restore_data(table, tab_name)
            print(f"--- Finished restoring {table} (Success: {results[table]}) ---")
        print("Finished restoring all tables.")
        return results

# Singleton instance
_instance = None

def get_sync_instance():
    """Get the singleton instance of GoogleSheetsSync."""
    global _instance
    if _instance is None:
        try:
            _instance = GoogleSheetsSync()
        except Exception as e:
            print(f"Failed to initialize GoogleSheetsSync instance: {e}")
            # Optionally, handle this case, e.g., by returning None or raising exception
            _instance = None # Ensure it stays None if init fails
    return _instance

def sync_on_data_change(table_name):
    """Sync a specific table when data changes."""
    sync = get_sync_instance()
    if sync:
        return sync.sync_data(table_name)
    else:
        print("Sync instance not available. Cannot sync.")
        return False

def sync_all():
    """Sync all tables."""
    sync = get_sync_instance()
    if sync:
        return sync.sync_all_data()
    else:
        print("Sync instance not available. Cannot sync all.")
        return False

def restore_table(table_name, tab_name=None):
    """Restore a specific table from Google Sheets."""
    sync = get_sync_instance()
    if sync:
        return sync.restore_data(table_name, tab_name)
    else:
        print("Sync instance not available. Cannot restore table.")
        return False

def restore_all(tab_name=None):
    """Restore all tables from Google Sheets."""
    sync = get_sync_instance()
    if sync:
        return sync.restore_all_data(tab_name)
    else:
        print("Sync instance not available. Cannot restore all.")
        return False

# Test the connection and basic sync/restore if this script is run directly
if __name__ == "__main__":
    print("Running Google Sheets Sync Test...")
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
        print("Connection failed! Check credentials and API access.")

