"""This script sets up a Flask server that listens for POST requests on specific endpoints."""  # noqa: D205
import json
import logging
import os
from io import BytesIO

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google.genai import Client, types
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 從 .env 文件中載入配置
load_dotenv()

# 設定上傳目錄
SAVE_MP3 = os.getenv("SAVE_MP3", "./saved_mp3")
os.makedirs(SAVE_MP3, exist_ok=True)

# 設定日誌系統
LOG_FILE = "server.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def prompt_transform(prompt):
    """將提示轉換為安全的文件名."""
    basename = prompt
    if len(basename) > 50:
        basename = basename[:50]
    return secure_filename(basename)

def generate_and_save_images(prompt, num_images=1):
    """生成圖片並保存到指定目錄."""
    save_dir = os.getenv("SAVE_IMAGES_DIR")
    if not save_dir:
        raise ValueError("找不到 SAVE_IMAGES_DIR，請確認 .env 檔")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("找不到 GEMINI_API_KEY，請確認 .env 檔")

    os.makedirs(save_dir, exist_ok=True)
    basename = prompt_transform(prompt)

    client = Client(api_key=api_key)
    response = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=num_images, aspectRatio="16:9")
    )

    saved_files = []
    for idx, generated_image in enumerate(response.generated_images):
        image = Image.open(BytesIO(generated_image.image.image_bytes))
        file_path = os.path.join(save_dir, f"{basename}_{idx+1}.png")
        image.save(file_path)
        saved_files.append(file_path)
        print(f"Image saved as {file_path}")

    return saved_files

@app.route('/save_mp3', methods=['POST'])
def save_mp3():
    """Handle the TTS request, generate MP3, and save it to the server."""
    logger.info("Received request to /save_mp3")
    data = request.get_json()
    jobj = data.get("jobj")
    if not jobj:
        logger.warning("No jobj provided in the request")
        return jsonify({"error": "未提供 jobj"}), 400

    try:
        # 檢查檔案是否已存在
        basename = prompt_transform(jobj.get("input"))
        filename = os.path.join(SAVE_MP3, f"{basename}.mp3")
        if os.path.exists(filename):
            logger.info(f"MP3 file already exists at {filename}, skipping generation")
            return jsonify({
                "status": "success",
                "message": "File already exists",
                "saved_path": filename,
                "file_size": os.path.getsize(filename)
            }), 200

        # 發送 TTS 請求
        tts_url = "https://api.openai.com/v1/audio/speech"
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return jsonify({"error": "找不到 OPENAI_API_KEY，請確認 .env 檔"}), 500

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info("Sending TTS request to OpenAI API")
        tts_response = requests.post(tts_url, headers=headers, json=jobj)
        tts_response.raise_for_status()

        # 保存 MP3 檔案
        with open(filename, "wb") as f:
            f.write(tts_response.content)

        logger.info(f"MP3 file saved successfully at {filename}")
        return jsonify({
            "status": "success",
            "saved_path": filename,
            "file_size": os.path.getsize(filename)
        }), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"TTS request failed: {str(e)}")
        return jsonify({"error": f"TTS 請求失敗: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate-and-save-images', methods=['POST'])
def generate_and_save_images_route():
    """Flask 路由：生成圖片並保存到指定目錄."""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        num_images = 1  # 固定為 1

        if not prompt:
            return jsonify({'error': '缺少 prompt 參數'}), 400

        save_dir = os.getenv("SAVE_IMAGES_DIR")
        if not save_dir:
            raise ValueError("找不到 SAVE_IMAGES_DIR，請確認 .env 檔")
        os.makedirs(save_dir, exist_ok=True)

        basename = prompt_transform(prompt)
        file_path = os.path.join(save_dir, f"{basename}_1.png")

        # 檢查檔案是否存在
        if os.path.exists(file_path):
            logger.info(f"Image file already exists: {file_path}")
            return jsonify({
                'message': 'Image already exists',
                'file': file_path
            }), 200

        # 生成並保存圖片
        saved_files = generate_and_save_images(prompt, num_images)
        return jsonify({'message': 'Image generated and saved successfully', 'files': saved_files}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload-json', methods=['POST'])
def upload_json():
    """Handle JSON file upload and process its content."""
    logger.info("Received request to /upload-json")
    if 'jsonFile' not in request.files:
        logger.warning("No file part in the request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['jsonFile']
    if file.filename == '':
        logger.warning("No file selected for upload")
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith('.json'):
        logger.warning("Invalid file type uploaded")
        return jsonify({"error": "Invalid file type. Only .json files are allowed."}), 400

    try:
        # Load and validate JSON
        data = json.load(file)
        if not validate_format(data):
            logger.warning("Invalid JSON format")
            return jsonify({"error": "Invalid JSON format"}), 400

        # Process content array
        results = []
        for item in data.get("content", []):
            narration = item.get("Narration", "")
            speak_instructions = item.get("speak_instructions", "")
            tts_payload = {
                "model": "gpt-4o-mini-tts",
                "voice": "alloy",
                "input": narration,
            }
            if speak_instructions:
                tts_payload["instructions"] = speak_instructions

            # Call /save_mp3 route
            logger.info(f"Calling /save_mp3 for narration: {narration}")
            response = call_save_mp3(tts_payload)
            results.append(response)

        logger.info("JSON file processed successfully")
        return jsonify({"status": "success", "results": results}), 200

    except json.JSONDecodeError:
        logger.error("Invalid JSON file uploaded")
        return jsonify({"error": "Invalid JSON file"}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def validate_format(data):
    """Validate if the JSON matches the required <format>."""
    required_keys = {"language", "title", "content"}
    if not isinstance(data, dict) or not required_keys.issubset(data.keys()):
        return False

    if not isinstance(data["content"], list):
        return False

    for item in data["content"]:
        if not isinstance(item, dict) or "Narration" not in item or "speak_instructions" not in item:
            return False

    return True

def call_save_mp3(payload):
    """Call the /save_mp3 route with the generated payload."""
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post("http://localhost:9125/save_mp3", json={"jobj": payload}, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to call /save_mp3: {str(e)}"}

@app.route('/')
def index():
    """Serve the UI for the root route."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9125, debug=True)