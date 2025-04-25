import unittest
from unittest.mock import patch, MagicMock
from app import app
import json
import io

class TestUploadJson(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.requests.post')
    def test_upload_json_with_mp3_modes(self, mock_post):
        # Mock the response for /save_mp3
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}

        # Sample JSON input
        sample_json = {
            "title": "Test Title",
            "content": [
                {"No": "01", "caption": "Caption 1", "Narration": "Narration 1"},
                {"No": "02", "caption": "Caption 2", "Narration": "Narration 2"}
            ],
            "mp3_modes": [True, False]
        }

        # Use BytesIO to simulate file upload
        json_file = io.BytesIO(json.dumps(sample_json).encode('utf-8'))
        json_file.name = 'test.json'

        response = self.app.post('/upload-json',
                                 data={"jsonFile": (json_file, 'test.json')},
                                 content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'success')

        # Ensure only the first item was processed
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('Narration 1', json.dumps(kwargs['json']))
        self.assertNotIn('Narration 2', json.dumps(kwargs['json']))

    def test_upload_json_invalid_format(self):
        # Invalid JSON input
        invalid_json = io.BytesIO(b"{")  # Malformed JSON
        invalid_json.name = 'test.json'

        response = self.app.post('/upload-json',
                                 data={"jsonFile": (invalid_json, 'test.json')},
                                 content_type='multipart/form-data')

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)

if __name__ == '__main__':
    unittest.main()