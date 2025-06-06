import sys
sys.path.append('/home/ubuntu/marketing_tracker_template')

# Import the hooked function
from data_hooks import add_marketing_activity
from utils_with_edit_delete import initialize_database, read_yaml
import os

# Ensure data directory and files exist
print("Initializing database (if needed)...")
initialize_database()

# Define dummy data
marketer = "admin"
prospect = "Test Prospect Inc."
location = "Test City"
contact_person = "John Doe"
position = "Manager"
phone = "123-456-7890"
email = "john.doe@test.com"
date = "2025-05-31"
type = "Initial Call"
desc = "Test activity to validate sync."

print(f"\nAttempting to add marketing activity for {prospect}...")

# Call the hooked function to add data and trigger sync
success, message, activity_id = add_marketing_activity(
    marketer, prospect, location, contact_person, position, phone, email, date, type, desc
)

print(f"\nResult of adding activity:")
print(f"  Success: {success}")
print(f"  Message: {message}")
print(f"  Activity ID: {activity_id}")

# Verify local YAML file content
if success:
    print("\nVerifying local YAML file content...")
    yaml_path = os.path.join("data", "marketing_activities.yaml")
    data = read_yaml(yaml_path)
    if data and "marketing_activities" in data and data["marketing_activities"]:
        print(f"Found {len(data['marketing_activities'])} entries in {yaml_path}.")
        print("Last entry:")
        print(data["marketing_activities"][-1])
        if data["marketing_activities"][-1]["id"] == activity_id:
            print("Local YAML file updated correctly with the new activity under 'marketing_activities' key.")
        else:
            print("Error: New activity not found or ID mismatch in local YAML.")
    else:
        print(f"Error: Could not read or find 'marketing_activities' key with data in {yaml_path}.")
else:
    print("\nSkipping YAML verification due to add failure.")

print("\nValidation script finished. Check logs above for sync status messages from google_sheets_sync.py.")

