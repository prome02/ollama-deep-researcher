import unittest
from unittest.mock import patch, MagicMock
from utils import generate_audio_file

class TestGenerateAudioFile(unittest.TestCase):

    @patch('utils.requests.post')
    def test_generate_audio_file_success(self, mock_post):
        # Mock a successful API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b"audio content"

        jobj = {"input": "Test narration"}
        api_key = "test_api_key"
        tts_url = "https://api.openai.com/v1/audio/speech"

        result = generate_audio_file(jobj, api_key, tts_url)

        self.assertEqual(result, b"audio content")
        mock_post.assert_called_once_with(
            tts_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=jobj
        )

    @patch('utils.requests.post')
    def test_generate_audio_file_failure(self, mock_post):
        # Mock a failed API response
        mock_post.return_value.status_code = 400
        mock_post.return_value.raise_for_status.side_effect = Exception("Bad Request")

        jobj = {"input": "Test narration"}
        api_key = "test_api_key"
        tts_url = "https://api.openai.com/v1/audio/speech"

        with self.assertRaises(Exception) as context:
            generate_audio_file(jobj, api_key, tts_url)

        self.assertIn("Bad Request", str(context.exception))
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()