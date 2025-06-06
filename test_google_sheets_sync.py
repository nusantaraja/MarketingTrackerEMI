import unittest
from unittest.mock import Mock, patch
from google_sheets_sync import GoogleSheetsSync

class TestGoogleSheetsSync(unittest.TestCase):
    def setUp(self):
        self.sync = GoogleSheetsSync()
        
    def test_sync_data_with_valid_table(self):
        with patch('google_sheets_sync.load_yaml_data') as mock_load:
            with patch.object(self.sync, '_update_sheet') as mock_update:
                mock_load.return_value = [{'id': 1, 'name': 'Test'}]
                self.sync.sync_data('users')
                mock_load.assert_called_once_with('users')
                mock_update.assert_called_once()

    def test_sync_data_with_empty_table(self):
        with patch('google_sheets_sync.load_yaml_data') as mock_load:
            with patch.object(self.sync, '_update_sheet') as mock_update:
                mock_load.return_value = []
                self.sync.sync_data('activities')
                mock_load.assert_called_once_with('activities')
                mock_update.assert_called_once()

    def test_sync_data_with_invalid_table(self):
        with patch('google_sheets_sync.load_yaml_data') as mock_load:
            mock_load.side_effect = FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                self.sync.sync_data('nonexistent_table')

    def test_sync_data_with_malformed_yaml(self):
        with patch('google_sheets_sync.load_yaml_data') as mock_load:
            mock_load.side_effect = yaml.YAMLError
            with self.assertRaises(yaml.YAMLError):
                self.sync.sync_data('corrupted_table')

if __name__ == '__main__':
    unittest.main()
