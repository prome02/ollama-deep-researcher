import logging
import os
import traceback  # 新增 traceback 模組
import time
from threading import Thread
from flask import Flask, json, jsonify, render_template, request, session
from werkzeug.utils import secure_filename

from combine_script import combine_media
from dotenv import load_dotenv

from utils import (
    call_generate_and_save_images,
    call_save_mp3,
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
    try:
        data = request.get_json()
        jobj = data.get("jobj")
        save_dir = data.get("save_dir")
        if not jobj:
            logger.warning("No jobj provided in the request")
            return jsonify({"error": "未提供 jobj"}), 400

        return call_save_mp3(jobj, save_dir)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Unexpected error: {str(e)}\n{tb}")
        return jsonify({"error": str(e), "details": tb}), 500

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

        # Process content array
        results = []
        for item in data.get("content", []):
            caption = item.get("caption")
            if not caption:
                logger.error("Caption is missing or invalid in one of the content items")
                return jsonify({"error": "Caption is missing or invalid"}), 400

            caption = secure_filename(caption)
            db_dir = os.path.join(da_dir, caption)
            os.makedirs(db_dir, exist_ok=True)

            # 呼叫 /save_mp3
            narration = item.get("Narration", "")
            speak_instructions = item.get("speak_instructions", "")
            prompt = item.get("prompt", "")

            tts_payload = {
                "model": "gpt-4o-mini-tts",
                "voice": "alloy",
                "input": narration,
            }
            if speak_instructions:
                tts_payload["instructions"] = speak_instructions

            logger.info(f"Calling /save_mp3 for narration: {narration[:30]}")
            tts_response = call_save_mp3(tts_payload, db_dir)
            results.append({"save_mp3": tts_response})

            # 呼叫 /generate-and-save-images
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

        # Start background process to handle folder
        thread = Thread(target=update_progress, args=(folder_path,))
        thread.start()

        return jsonify({'status': 'success', 'message': 'Processing started', 'generateFinalVideo': generate_final_video}), 200
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