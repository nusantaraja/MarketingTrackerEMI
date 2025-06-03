import sys
import os
sys.path.append(os.getcwd())
from utils_with_edit_delete import add_marketing_activity, get_all_marketing_activities, DATA_DIR, ACTIVITIES_FILENAME
from datetime import date

# Define test data
test_username = "test_marketer"
test_prospect = "Test Prospect Status"
test_location = "Test Location"
test_person = "Test Person"
test_position = "Test Position"
test_phone = "081234567890"
test_email = "test@example.com"
test_date = date.today()
test_type = "Meeting"
test_desc = "Test description for status add."
test_status = "dalam_proses" # Test adding with a non-default status

print(f"Attempting to add activity with status: {test_status}")

# Add the activity
success, message, activity_id = add_marketing_activity(
    test_username,
    test_prospect,
    test_location,
    test_person,
    test_position,
    test_phone,
    test_email,
    test_date,
    test_type,
    test_desc,
    test_status
)

if not success:
    print(f"Validation Failed: Failed to add activity. Message: {message}")
    sys.exit(1)

print(f"Activity added successfully with ID: {activity_id}")

# Verify the added activity
print("Verifying the added activity...")
activities = get_all_marketing_activities()
added_activity = next((act for act in activities if act["id"] == activity_id), None)

if not added_activity:
    print(f"Validation Failed: Could not find the added activity with ID {activity_id} in the data file.")
    sys.exit(1)

# Check the status
if added_activity.get("status") == test_status:
    print(f"Validation Successful: Activity status correctly saved as 	{test_status}	.")
else:
    print(f"Validation Failed: Activity status was saved as 	{added_activity.get('status')}	, expected 	{test_status}	.")
    sys.exit(1)

sys.exit(0)

