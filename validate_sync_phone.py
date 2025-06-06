import sys
sys.path.append(
    '/home/ubuntu/marketing_tracker_template')  # Ensure the project root is in the path

# Import the hooked function and utilities
from data_hooks import add_marketing_activity
from utils_with_edit_delete import initialize_database, read_yaml
import os

# Ensure data directory and files exist
print("Initializing database (if needed)...")
initialize_database()

# Define dummy data with Indonesian phone number format
marketer = "admin"
prospect = "Test Prospect Indo"
location = "Jakarta"
contact_person = "Budi Santoso"
position = "Direktur"
phone = "+6281234567890"  # Phone number with +62 prefix
email = "budi.santoso@testindo.com"
date = "2025-05-31"
type = "Meeting"
desc = "Test activity with Indonesian phone number to validate sync and formatting."

print(f"\nAttempting to add marketing activity for {prospect} with phone {phone}...")

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
        last_entry = data["marketing_activities"][-1]
        print(last_entry)
        if last_entry["id"] == activity_id:
            print(
                "Local YAML file updated correctly with the new activity under 'marketing_activities' key."
            )
            # Check if phone number in YAML is still the original string
            if last_entry.get("contact_phone") == phone:
                print(f"Phone number correctly stored as string ",
                      f"\"{phone}\" in local YAML.")
            else:
                print(
                    f"Error: Phone number mismatch in local YAML. Expected ",
                    f"\"{phone}\", got \"{last_entry.get('contact_phone')}\"."
                )
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
print("Verify manually in Google Sheets if the phone number was recorded as a number without the + prefix.")

