import logging
import os
import time
import traceback  # 新增 traceback 模組

import requests
from dotenv import load_dotenv
from flask import Flask, json, jsonify, render_template, request, session
from werkzeug.utils import secure_filename

from combine_script import combine_media
from utils import (
    call_generate_and_save_images,
    validate_format,
)

app = Flask(__name__)

# 從 .env 文件中載入配置
load_dotenv()

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

progress = {}  # 用於存儲進度狀態

SAVE_MP3 = os.getenv("SAVE_MP3", "./saved_mp3")
os.makedirs(SAVE_MP3, exist_ok=True)

def prompt_transform(prompt):
    """將提示轉換為安全的文件名."""
    basename = prompt
    if len(basename) > 50:
        basename = basename[:50]
    return secure_filename(basename)

def update_progress(folder_path):
    """模擬進度更新的後台任務"""
    global progress
    progress[folder_path] = 0
    for i in range(1, 101):
        time.sleep(0.1)  # 模擬耗時操作
        progress[folder_path] = i
    progress[folder_path] = 100

@app.route('/save_mp3', methods=['POST'])
def save_mp3():
    """Handle the TTS request, generate MP3, and save it to the server."""
    logger.info("Received request to /save_mp3")
    data = request.get_json()
    jobj = data.get("jobj")
    save_dir = data.get("save_dir", SAVE_MP3)
    if not jobj:
        logger.warning("No jobj provided in the request")
        return jsonify({"error": "未提供 jobj"}), 400

    try:
        # 檢查檔案是否已存在
        basename = prompt_transform(jobj.get("input"))
        filename = os.path.join(save_dir, f"{basename}.mp3")
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
        os.makedirs(save_dir, exist_ok=True)
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
        save_dir = data.get("save_dir")

        if not prompt:
            return jsonify({'error': '缺少 prompt 參數'}), 400

        return call_generate_and_save_images(prompt, save_dir)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Unexpected error: {str(e)}\n{tb}")
        return jsonify({"error": str(e), "details": tb}), 500

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

        # 從 .env 獲取初始資料夾位置
        init_dir = os.getenv("INIT_DIR")
        if not init_dir:
            raise ValueError("找不到 INIT_DIR，請確認 .env 檔")
        os.makedirs(init_dir, exist_ok=True)

        # 根據 JSON 文件的主檔名創建資料夾
        json_filename = secure_filename(file.filename.rsplit('.', 1)[0])  # 去掉副檔名
        da_dir = os.path.join(init_dir, json_filename)
        os.makedirs(da_dir, exist_ok=True)

        # Extract relevant data from the Response objects before appending to results
        results = []
        for item in data.get("content", []):
            caption = item.get("caption")
            if not caption:
                logger.error("Caption is missing or invalid in one of the content items")
                return jsonify({"error": "Caption is missing or invalid"}), 400

            caption = secure_filename(caption)
            db_dir = os.path.join(da_dir, caption)
            os.makedirs(db_dir, exist_ok=True)

            # Call /save_mp3
            narration = item.get("Narration", "")
            speak_instructions = item.get("speak_instructions", "")
            voice_actor = item.get("voice_actor", "alloy")

            tts_payload = {
                "model": "gpt-4o-mini-tts",
                "voice": voice_actor,
                "input": narration,
            }
            if speak_instructions:
                tts_payload["instructions"] = speak_instructions

            logger.info(f"Calling /save_mp3 for narration: {narration[:30]}")

            headers = {"Content-Type": "application/json"}
            tts_response = requests.post("http://localhost:9125/save_mp3", json={"jobj": tts_payload, "save_dir": db_dir}, headers=headers)
            tts_response_data = {
                "status_code": tts_response.status_code,
                "response": tts_response.json() if tts_response.status_code == 200 else tts_response.text
            }
            results.append({"save_mp3": tts_response_data})

            # Call /generate-and-save-images
            prompt = item.get("prompt", "")
            if prompt:
                logger.info(f"Calling /generate-and-save-images for prompt: {prompt[:30]}")
                image_response = call_generate_and_save_images(prompt, db_dir)
                results[-1]["generate_and_save_images"] = image_response

        logger.info("JSON file processed successfully")
        return jsonify({"status": "success", "results": results}), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Unexpected error: {str(e)}\n{tb}")
        return jsonify({"error": str(e), "details": tb}), 500

@app.route('/process-folder', methods=['POST'])
def process_folder():
    """Process the selected folder to create a video from .mp3 and .png files."""
    try:
        data = request.get_json()
        folder_path = data.get('folderPath')
        generate_final_video = data.get('generateFinalVideo', False)  # Get the checkbox value

        # Log the checkbox value
        logger.info(f"Generate final video: {generate_final_video}")

        result = combine_media(folder_path, generate_final_video)
        return jsonify({'status': 'success', 'message': 'Folder processed successfully', 'details': result, 
        'generateFinalVideo': generate_final_video}), 200

        # Start background process to handle folder
        # thread = Thread(target=update_progress, args=(folder_path,))
        # thread.start()

        # return jsonify({'status': 'success', 'message': 'Processing started', 'generateFinalVideo': generate_final_video}), 200
    except Exception as e:
        logger.error(f"Error processing folder: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<folder_path>', methods=['GET'])
def get_progress(folder_path):
    """返回指定文件夾的進度狀態"""
    global progress
    current_progress = progress.get(folder_path, 0)
    return jsonify({'progress': current_progress}), 200

@app.route('/save-text', methods=['POST'])
def save_text():
    """Handle request to save text data to a file."""
    try:
        # Parse JSON data from the request
        data = request.get_json()
        filename = data.get('filename')
        content = data.get('data')

        if not filename or not content:
            return jsonify({'error': 'Missing filename or data'}), 400

        # Secure the filename to prevent directory traversal attacks
        safe_filename = secure_filename(filename)
        safe_filename = os.path.join("./content/deep_research", safe_filename)

        # Save the content to a file
        with open(safe_filename, 'w', encoding='utf-8') as file:
            file.write(content)

        return jsonify({'status': 'success', 'message': f'File {safe_filename} saved successfully.'}), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Unexpected error: {str(e)}\n{tb}")
        return jsonify({'error': str(e), 'details': tb}), 500

@app.route('/')
def index():
    """Serve the UI for the root route."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9125, debug=True)