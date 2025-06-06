import sys
import os
import yaml
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Ensure data directory exists
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Import the hook for manual sync
from data_hooks import manual_sync_all
from utils_with_edit_delete import write_yaml_data, get_wib_now_str

# --- Test Data ---
initial_activities = [
    {
        "id": "act_001",
        "marketer_username": "test_user",
        "prospect_name": "Initial Prospect 1",
        "contact_phone": "081234567890",
        "activity_date": "2024-06-01",
        "status": "baru",
        "created_at": get_wib_now_str(),
        "updated_at": get_wib_now_str(),
        # Add other required fields with dummy data
        "prospect_location": "", "contact_person": "", "contact_position": "",
        "contact_email": "", "activity_type": "", "description": "Initial"
    }
]

new_activities = [
    {
        "id": "act_002",
        "marketer_username": "test_user",
        "prospect_name": "New Prospect 2",
        "contact_phone": "08111222333",
        "activity_date": "2024-06-04",
        "status": "baru",
        "created_at": get_wib_now_str(),
        "updated_at": get_wib_now_str(),
        # Add other required fields with dummy data
        "prospect_location": "", "contact_person": "", "contact_position": "",
        "contact_email": "", "activity_type": "", "description": "New"
    }
]

# --- Test Functions ---
def write_test_data(activities):
    "Writes a list of activities to the YAML file."
    write_yaml_data("marketing_activities", {"marketing_activities": activities})
    print(f"Wrote {len(activities)} activities to marketing_activities.yaml")

def run_sync_test():
    print("--- Test: Initial Sync ---")
    write_test_data(initial_activities)
    print("Running initial manual sync (incremental=True)...")
    # Note: This will fail if credentials aren't set up, but we check the logic flow
    try:
        success1, message1 = manual_sync_all(incremental=True)
        print(f"Initial Sync Result: Success={success1}, Message=\"{message1}\"")
        # We expect this to try and sync 1 record
    except Exception as e:
        print(f"Initial Sync failed (as expected without creds?): {e}")

    print("\n--- Test: Second Sync with New Data ---")
    all_activities = initial_activities + new_activities
    write_test_data(all_activities)
    print("Running second manual sync (incremental=True)...")
    try:
        success2, message2 = manual_sync_all(incremental=True)
        print(f"Second Sync Result: Success={success2}, Message=\"{message2}\"")
        # We expect this to try and sync only the 1 *new* record
        if "appended 1 new rows for marketing_activities incrementally" in message2:
             print("VALIDATION PASSED: Second sync message indicates only 1 new row was processed.")
        elif "No new records found" in message2:
             print("VALIDATION INFO: Second sync message indicates no new rows were found (might happen if sheet already had data or IDs matched). Check logic.")
        elif "appended 2 rows" in message2: # Check if it appended all
             print("VALIDATION FAILED: Second sync message indicates all rows were processed, not incremental.")
        else:
             print(f"VALIDATION INFO: Unexpected message from second sync: {message2}")

    except Exception as e:
        print(f"Second Sync failed (as expected without creds?): {e}")

if __name__ == "__main__":
    run_sync_test()

