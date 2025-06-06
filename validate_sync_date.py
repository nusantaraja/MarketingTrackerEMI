import sys
sys.path.append(
    '/home/ubuntu/marketing_tracker_template')  # Ensure the project root is in the path

# Import the hooked functions and utilities
from data_hooks import add_marketing_activity, add_followup
from utils_with_edit_delete import initialize_database, read_yaml
import os
from datetime import date, timedelta

# Ensure data directory and files exist
print("Initializing database (if needed)...")
initialize_database()

# --- Test Adding Activity --- 

# Define dummy data for activity
marketer_act = "admin"
prospect_act = "Test Prospect Date Format"
location_act = "Bandung"
contact_person_act = "Citra Lestari"
position_act = "Marketing Mgr"
phone_act = "08111222333"
email_act = "citra.lestari@testdate.com"
activity_date_act = date.today() # Use today's date
date_str_act = activity_date_act.strftime('%Y-%m-%d')
type_act = "Demo"
desc_act = "Test activity to validate date formatting in sync."

print(f"\nAttempting to add marketing activity for {prospect_act} with date {date_str_act}...")

# Call the hooked function to add data and trigger sync
success_act, message_act, activity_id = add_marketing_activity(
    marketer_act, prospect_act, location_act, contact_person_act, position_act, 
    phone_act, email_act, activity_date_act, type_act, desc_act
)

print(f"\nResult of adding activity:")
print(f"  Success: {success_act}")
print(f"  Message: {message_act}")
print(f"  Activity ID: {activity_id}")

# --- Test Adding Followup (if activity added successfully) --- 

if success_act and activity_id:
    # Define dummy data for followup
    marketer_fu = "admin"
    followup_date_fu = date.today() + timedelta(days=1)
    followup_date_str = followup_date_fu.strftime('%Y-%m-%d')
    notes_fu = "Follow up after demo."
    next_action_fu = "Send proposal"
    next_followup_date_fu = date.today() + timedelta(days=7)
    next_followup_date_str = next_followup_date_fu.strftime('%Y-%m-%d')
    interest_level_fu = "High"
    status_update_fu = "follow-up"

    print(f"\nAttempting to add followup for activity {activity_id} with date {followup_date_str}...")

    # Call the hooked function to add followup and trigger sync
    success_fu, message_fu = add_followup(
        activity_id, marketer_fu, followup_date_fu, notes_fu, 
        next_action_fu, next_followup_date_fu, interest_level_fu, status_update_fu
    )

    print(f"\nResult of adding followup:")
    print(f"  Success: {success_fu}")
    print(f"  Message: {message_fu}")
else:
    print("\nSkipping followup test because activity creation failed or returned no ID.")

# --- Verification --- 

print(
    "\nValidation script finished. Check logs above for sync status messages from google_sheets_sync.py."
)
# Corrected the final print statement to close the string literal and parenthesis
print("IMPORTANT: Please manually verify in Google Sheets if the date columns "
      "('activity_date', 'created_at', 'updated_at' in Activities tab; "
      "'followup_date', 'next_followup_date', 'created_at' in Followups tab) "
      "are now formatted correctly (e.g., YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) "
      "and not as serial numbers.")

