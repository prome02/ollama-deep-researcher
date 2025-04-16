import os

import requests
from werkzeug.utils import secure_filename


def call_save_mp3(payload, save_dir):
    """Call the /save_mp3 route with the generated payload and save directory."""
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post("http://localhost:9125/save_mp3", json={"jobj": payload, "save_dir": save_dir}, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to call /save_mp3: {str(e)}"}

def call_generate_and_save_images(prompt, save_dir):
    """Call the /generate-and-save-images route with the given prompt and save directory."""
    try:
        headers = {"Content-Type": "application/json"}
        payload = {"prompt": prompt, "save_dir": save_dir}
        response = requests.post("http://localhost:9125/generate-and-save-images", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to call /generate-and-save-images: {str(e)}"}

def validate_format(data):
    """Validate if the JSON matches the required format."""
    required_keys = {"language", "title", "content"}
    if not isinstance(data, dict) or not required_keys.issubset(data.keys()):
        return False

    if not isinstance(data["content"], list):
        return False

    for item in data["content"]:
        if not isinstance(item, dict) or "Narration" not in item or "speak_instructions" not in item:
            return False

    return True