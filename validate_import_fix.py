import sys
import os

sys.path.append('/home/ubuntu/marketing_tracker_template')

print("Attempting to import app_with_sheets...")
try:
    # We only need to check if the import works, no need to run the full app
    from app_with_sheets import add_google_sheets_sync_ui # Import something specific
    print("Import successful. The ImportError related to 'check_login' seems resolved.")
except ImportError as e:
    print(f"Import FAILED: {e}")
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")

