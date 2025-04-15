"""This script sets up a Flask server that listens for POST requests on specific endpoints."""  # noqa: D205
import os
import requests
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from google.genai import Client, types
from PIL import Image
from io import BytesIO

app = Flask(__name__)

# 從 .env 文件中載入配置
load_dotenv()

# 設定上傳目錄
SAVE_MP3 = os.getenv("SAVE_MP3", "./saved_mp3")
os.makedirs(SAVE_MP3, exist_ok=True)

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
    data = request.get_json()
    jobj = data.get("jobj")
    if not jobj:
        return jsonify({"error": "未提供 jobj"}), 400

    try:
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

        basename = prompt_transform(jobj.get("input"))
        filename = os.path.join(SAVE_MP3, f"{basename}.mp3")
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

@app.route('/generate-and-save-images', methods=['POST'])
def generate_and_save_images_route():
    """Flask 路由：生成圖片並保存到指定目錄."""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        num_images = data.get('num_images', 1)

        if not prompt:
            return jsonify({'error': '缺少 prompt 參數'}), 400

        saved_files = generate_and_save_images(prompt, num_images)
        return jsonify({'message': 'Images generated and saved successfully', 'files': saved_files}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9125, debug=True)