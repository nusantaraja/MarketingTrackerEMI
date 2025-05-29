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
from oauth2client.service_account import ServiceAccountCredentials

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
        """Connect to Google Sheets API."""
        try:
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            # Authenticate using the service account credentials
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, scope)
            
            # Create gspread client
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            print(f"Successfully connected to Google Sheets: {self.spreadsheet.title}")
            return True
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            return False
    
    def get_current_month_tab_name(self):
        """Get the tab name for the current month."""
        now = datetime.now()
        return f"{now.strftime('%Y_%m')}"
    
    def ensure_monthly_tab_exists(self):
        """Ensure that a tab exists for the current month."""
        tab_name = self.get_current_month_tab_name()
        
        # Check if the tab already exists
        try:
            self.spreadsheet.worksheet(tab_name)
            print(f"Tab {tab_name} already exists.")
            return tab_name
        except gspread.exceptions.WorksheetNotFound:
            # Create a new tab for the current month
            print(f"Creating new tab for {tab_name}")
            self.spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=26)
            
            # Initialize the tab with headers for each table
            self._initialize_monthly_tab(tab_name)
            return tab_name
    
    def _initialize_monthly_tab(self, tab_name):
        """Initialize a new monthly tab with headers for each table."""
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
                worksheet.update_cell(row, 1, "ID")
                for col, header in enumerate(headers, start=2):
                    worksheet.update_cell(row, col, header)
                row += 1
            
            # Add empty row after each table
            row += 20  # Space for data
            row += 1   # Empty row separator
    
    def _get_table_headers(self, table):
        """Get the headers for a specific table."""
        try:
            # Load the YAML file to get the structure
            file_path = os.path.join(DATA_DIR, f"{table}.yaml")
            if not os.path.exists(file_path):
                return []
                
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            
            # If data exists, get the keys from the first item
            if data and isinstance(data, list) and len(data) > 0:
                return list(data[0].keys())
            elif data and isinstance(data, dict):
                # For config or other dict-based files
                return list(data.keys())
            return []
        except Exception as e:
            print(f"Error getting headers for {table}: {e}")
            return []
    
    def sync_data(self, table_name, force_sync=False):
        """Sync data from a specific table to Google Sheets."""
        try:
            # Ensure we have a tab for the current month
            tab_name = self.ensure_monthly_tab_exists()
            worksheet = self.spreadsheet.worksheet(tab_name)
            
            # Load data from YAML file
            file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
                
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            
            # Find the section for this table in the worksheet
            cell_list = worksheet.findall(f"=== {table_name.upper()} ===")
            if not cell_list:
                print(f"Section for {table_name} not found in worksheet")
                return False
            
            # Get the row where the table starts
            start_row = cell_list[0].row + 2  # +1 for header row, +1 to start at data
            
            # Convert data to a format suitable for Google Sheets
            if isinstance(data, list):
                # For list-based data (activities, followups, users)
                df = pd.DataFrame(data)
                values = [df.columns.tolist()] + df.values.tolist()
            elif isinstance(data, dict):
                # For dict-based data (config)
                df = pd.DataFrame(list(data.items()), columns=['Key', 'Value'])
                values = [df.columns.tolist()] + df.values.tolist()
            else:
                print(f"Unsupported data format for {table_name}")
                return False
            
            # Update the worksheet with the data
            if values:
                # Clear existing data in this section
                end_row = start_row + 19  # Maximum 20 rows per section
                worksheet.batch_clear([f"A{start_row}:Z{end_row}"])
                
                # Update with new data
                cell_range = f"A{start_row}:{chr(65 + len(values[0]) - 1)}{start_row + len(values) - 1}"
                worksheet.update(cell_range, values)
                
                print(f"Successfully synced {table_name} to Google Sheets")
                return True
            
            return False
        except Exception as e:
            print(f"Error syncing {table_name} to Google Sheets: {e}")
            return False
    
    def sync_all_data(self, force_sync=False):
        """Sync all tables to Google Sheets."""
        results = {}
        for table in TABLES:
            results[table] = self.sync_data(table, force_sync)
        return results
    
    def restore_data(self, table_name, tab_name=None):
        """Restore data from Google Sheets to local YAML file."""
        try:
            # If no tab name is provided, use the current month
            if not tab_name:
                tab_name = self.get_current_month_tab_name()
            
            # Get the worksheet
            try:
                worksheet = self.spreadsheet.worksheet(tab_name)
            except gspread.exceptions.WorksheetNotFound:
                print(f"Tab {tab_name} not found")
                return False
            
            # Find the section for this table in the worksheet
            cell_list = worksheet.findall(f"=== {table_name.upper()} ===")
            if not cell_list:
                print(f"Section for {table_name} not found in worksheet")
                return False
            
            # Get the row where the table starts
            start_row = cell_list[0].row + 1  # +1 for header row
            
            # Get the headers
            headers = worksheet.row_values(start_row)
            if not headers:
                print(f"No headers found for {table_name}")
                return False
            
            # Get the data rows
            data_rows = []
            row = start_row + 1
            while True:
                row_values = worksheet.row_values(row)
                if not row_values or not row_values[0] or row > start_row + 19:
                    break
                data_rows.append(row_values)
                row += 1
            
            # Convert to appropriate format
            if table_name == "config":
                # Config is a dictionary
                restored_data = {}
                for row in data_rows:
                    if len(row) >= 2:
                        restored_data[row[0]] = row[1]
            else:
                # Other tables are lists of dictionaries
                restored_data = []
                for row in data_rows:
                    item = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            item[header] = row[i]
                        else:
                            item[header] = ""
                    restored_data.append(item)
            
            # Save to YAML file
            file_path = os.path.join(DATA_DIR, f"{table_name}.yaml")
            with open(file_path, 'w') as file:
                yaml.dump(restored_data, file, default_flow_style=False)
            
            print(f"Successfully restored {table_name} from Google Sheets")
            return True
        except Exception as e:
            print(f"Error restoring {table_name} from Google Sheets: {e}")
            return False
    
    def restore_all_data(self, tab_name=None):
        """Restore all tables from Google Sheets."""
        results = {}
        for table in TABLES:
            results[table] = self.restore_data(table, tab_name)
        return results

# Singleton instance
_instance = None

def get_sync_instance():
    """Get the singleton instance of GoogleSheetsSync."""
    global _instance
    if _instance is None:
        _instance = GoogleSheetsSync()
    return _instance

def sync_on_data_change(table_name):
    """Sync a specific table when data changes."""
    sync = get_sync_instance()
    return sync.sync_data(table_name)

def sync_all():
    """Sync all tables."""
    sync = get_sync_instance()
    return sync.sync_all_data()

def restore_table(table_name, tab_name=None):
    """Restore a specific table from Google Sheets."""
    sync = get_sync_instance()
    return sync.restore_data(table_name, tab_name)

def restore_all(tab_name=None):
    """Restore all tables from Google Sheets."""
    sync = get_sync_instance()
    return sync.restore_all_data(tab_name)

# Test the connection if this script is run directly
if __name__ == "__main__":
    sync = GoogleSheetsSync()
    if sync.connect():
        print("Connection successful!")
        print("Syncing all data...")
        sync.sync_all_data()
    else:
        print("Connection failed!")
