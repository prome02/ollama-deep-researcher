import os
from io import BytesIO
from PIL import Image
from werkzeug.utils import secure_filename
from google.genai import Client, types
import requests


def call_save_mp3(payload, save_dir):
    """Call the /save_mp3 route with the generated payload and save directory."""
    try:
        # 原始程式碼（已註解）
        headers = {"Content-Type": "application/json"}
        response = requests.post("http://localhost:9125/save_mp3", json={"jobj": payload, "save_dir": save_dir}, headers=headers)
        response.raise_for_status()
        return response.json()

        # 模擬成功回應
        # filename = os.path.join(save_dir, f"{secure_filename(payload.get('input', 'default'))}.mp3")
        # return {
        #     "status": "success",
        #     "message": "Simulated MP3 generation success",
        #     "saved_path": filename,
        #     "file_size": 12345  # 模擬檔案大小
        # }
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to call /save_mp3: {str(e)}"}

def call_generate_and_save_images(prompt, save_dir):
    """Generate a single image based on the given prompt and save it to the specified directory."""
    try:
        # 確保 SAVE_IMAGES_DIR 存在
        if not save_dir:
            raise ValueError("Save directory is not specified")

        os.makedirs(save_dir, exist_ok=True)

        # 處理 prompt 並生成安全的文件名
        basename = secure_filename(prompt[:50])

        # return {
        #     "status": "test: success",
        #     "message": "test: Image generated successfully",
        #     "file": f"test: {save_dir}/{basename}.png"
        # }
        # 獲取 API 金鑰
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("找不到 GEMINI_API_KEY，請確認 .env 檔")

        # 初始化 Google GenAI 客戶端
        client = Client(api_key=api_key)
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1, aspectRatio="16:9")
        )

        # 保存生成的圖片
        generated_image = response.generated_images[0]  # 只取第一張圖片
        image = Image.open(BytesIO(generated_image.image.image_bytes))
        file_path = os.path.join(save_dir, f"{basename}.png")
        image.save(file_path)

        return {
            "status": "success",
            "message": "Image generated successfully",
            "file": file_path
        }
    except Exception as e:
        return {"error": f"Failed to generate image: {str(e)}"}

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