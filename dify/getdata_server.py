"""This script sets up a Flask server that listens for POST requests on various endpoints.
接收dify的json数据，保存为文件 (dify:優化小說內容流程).
"""  # noqa: D205
import os

import requests
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 設定上傳目錄
UPLOAD_FOLDER = './saved_mp3'
IMAGE_UPLOAD_FOLDER = './static/images'  # 圖片上傳目錄
GENERAL_UPLOAD_FOLDER = './uploads'  # 通用圖片上傳目錄
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERAL_UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = GENERAL_UPLOAD_FOLDER

def allowed_file(filename):
    """檢查文件是否為允許的圖片格式."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/save_mp3', methods=['POST'])
def save_mp3():
    """Handle the TTS request, generate MP3, and save it to the server."""
    data = request.get_json()
    jobj = data.get("jobj")
    if not jobj:
        return jsonify({"error": "未提供 jobj"}), 400

    try:
        # 使用 OpenAI TTS API 生成 MP3
        tts_url = "https://api.openai.com/v1/audio/speech"
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "找不到 OPENAI_API_KEY，請確認 .env 檔"}), 500

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        tts_response = requests.post(tts_url, headers=headers, json=jobj)
        tts_response.raise_for_status()

        # 保存 MP3 文件
        filename = os.path.join(UPLOAD_FOLDER, "output.mp3")
        with open(filename, "wb") as f:
            f.write(tts_response.content)

        return jsonify({
            "status": "success",
            "saved_path": filename,
            "file_size": os.path.getsize(filename)
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"TTS 請求失敗: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle the upload of a file via JSON data and save it to the server.

    Returns:
    -------
    Response
        A JSON response containing a success message and the saved filename, 
        or an error message in case of failure.
    """
    try:
        jobj = request.get_json()
        filename = jobj.get('filename')
        # 如果文件已存在，為文件名添加數字後綴
        if filename:
            i = 1
            while os.path.exists(filename):
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{i}{ext}"
                i += 1
        data = jobj.get('data')
        
        if not filename or not data:
            return jsonify({'error': 'Missing filename or data'}), 400
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        
        return jsonify({'message': 'File saved successfully', 'filename': filename}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_image', methods=['POST'])
def download_image():
    """Download an image from a given URL and save it to the server.

    Returns:
    -------
    Response
        A JSON response containing the status, saved file path, and file size, 
        or an error message in case of failure.
    """
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "未提供圖片 URL"}), 400

    try:
        filename = secure_filename(url.split('/')[-1])
        if not allowed_file(filename):
            return jsonify({"error": "不支援的圖片格式"}), 400

        response = requests.get(url, stream=True)
        response.raise_for_status()

        save_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        return jsonify({
            "status": "success",
            "saved_path": save_path,
            "file_size": os.path.getsize(save_path)
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"圖片下載失敗: {str(e)}"}), 500

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle the upload of an image file and save it to the server.

    Returns:
    -------
    Response
        A JSON response containing a success message and the saved file path, 
        or an error message in case of failure.
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    # 保存圖片到磁碟
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)
    
    return jsonify({'message': 'Image uploaded successfully', 'file_path': file_path})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9125, debug=True)