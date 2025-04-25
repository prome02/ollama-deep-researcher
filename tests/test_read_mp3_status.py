import unittest
from unittest.mock import patch, MagicMock
from app import app
import json

class TestReadMp3Status(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.requests.post')
    def test_read_mp3_status(self, mock_post):
        # Mock the response for /mp3-name-list
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = ["01Caption1", "02Caption2"]

        # Simulate JSON file upload
        sample_json = {
            "content": [
                {"No": "01", "caption": "Caption1"},
                {"No": "02", "caption": "Caption2"}
            ]
        }

        response = self.app.post('/mp3-name-list',
                                 data=json.dumps(sample_json),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data, ["01Caption1", "02Caption2"])

if __name__ == '__main__':
    unittest.main()