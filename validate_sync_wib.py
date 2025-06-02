import sys
sys.path.append(
    '/home/ubuntu/marketing_tracker_template')  # Ensure the project root is in the path

# Import the hooked function and utilities
from data_hooks import add_marketing_activity
from utils_with_edit_delete import initialize_database, read_yaml, get_current_timestamp
import os
from datetime import datetime
import pytz

# Ensure data directory and files exist
print("Initializing database (if needed)...")
initialize_database()

# Define dummy data
marketer = "admin"
prospect = "Test Prospect WIB"
location = "Jakarta"
contact_person = "Budi Santoso"
position = "Sales"
phone = "081234567890"
email = "budi.santoso@testwib.com"
date = "2025-06-01"
type = "Meeting"
desc = "Test activity to validate WIB timestamp recording."

print(f"\nAttempting to add marketing activity for {prospect}...")

# Record the approximate time *before* adding the activity (in WIB)
wib_tz = pytz.timezone("Asia/Bangkok")
time_before_add = datetime.now(wib_tz)

# Call the hooked function to add data and trigger sync
success, message, activity_id = add_marketing_activity(
    marketer, prospect, location, contact_person, position, phone, email, date, type, desc
)

# Record the approximate time *after* adding the activity (in WIB)
time_after_add = datetime.now(wib_tz)

print(f"\nResult of adding activity:")
print(f"  Success: {success}")
print(f"  Message: {message}")
print(f"  Activity ID: {activity_id}")

# Verify local YAML file content and timestamp
if success:
    print("\nVerifying local YAML file content and timestamp...")
    yaml_path = os.path.join("data", "marketing_activities.yaml")
    data = read_yaml(yaml_path)
    if data and "marketing_activities" in data and data["marketing_activities"]:
        print(f"Found {len(data['marketing_activities'])} entries in {yaml_path}.")
        print("Last entry:")
        last_entry = data["marketing_activities"][-1]
        print(last_entry)
        if last_entry["id"] == activity_id:
            print(
                "Local YAML file updated correctly with the new activity."
            )
            # Check the created_at timestamp
            created_at_str = last_entry.get("created_at")
            if created_at_str:
                try:
                    # Parse the timestamp string from YAML
                    created_at_dt = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
                    # Make it timezone-aware (assuming it was stored as WIB naive)
                    created_at_dt_wib_naive = wib_tz.localize(created_at_dt, is_dst=None)
                    
                    print(f"  Timestamp recorded in YAML: {created_at_str} (Assumed WIB)")
                    print(f"  Time range of test (WIB): {time_before_add.strftime('%Y-%m-%d %H:%M:%S')} - {time_after_add.strftime('%Y-%m-%d %H:%M:%S')}")

                    # Check if the recorded time falls within the test execution time range
                    # Allow a small buffer (e.g., a few seconds) if needed, but direct comparison is usually fine
                    if time_before_add <= created_at_dt_wib_naive <= time_after_add:
                        print("  SUCCESS: Recorded timestamp falls within the expected WIB time range.")
                    else:
                        print("  ERROR: Recorded timestamp is outside the expected WIB time range.")
                        
                except ValueError as e:
                    print(f"  ERROR: Could not parse recorded timestamp string: {created_at_str} - {e}")
                except Exception as e:
                     print(f"  ERROR: An unexpected error occurred during timestamp validation: {e}")
            else:
                print("  ERROR: created_at timestamp not found in the last entry.")
        else:
            print("Error: New activity not found or ID mismatch in local YAML.")
    else:
        print(
            f"Error: Could not read or find 'marketing_activities' key with data in {yaml_path}."
        )
else:
    print("\nSkipping YAML verification due to add failure.")

print(
    "\nValidation script finished. Check logs above for sync status messages from google_sheets_sync.py."
)
print("IMPORTANT: Please manually verify the timestamp columns (created_at, updated_at) in Google Sheets ",
      "to ensure they reflect the correct WIB time (UTC+7).")

