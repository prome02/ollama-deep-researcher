import os
from io import BytesIO

import ffmpeg
from google.genai import Client, types
from PIL import Image
from werkzeug.utils import secure_filename


def call_generate_and_save_images(prompt, save_dir):
    """Generate a single image based on the given prompt and save it to the specified directory."""
    try:
        # 確保 SAVE_IMAGES_DIR 存在
        if not save_dir:
            raise ValueError("Save directory is not specified")

        os.makedirs(save_dir, exist_ok=True)

        # 處理 prompt 並生成安全的文件名
        basename = secure_filename(prompt[:50])
        file_path = os.path.join(save_dir, f"{basename}.png")

        # 如果檔案已經存在，直接返回成功訊息
        if os.path.exists(file_path):
            return {
                "status": "success",
                "message": "Image already exists",
                "file": file_path
            }

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

def generate_video(mp3_path, png_path, output_path):
    """使用圖片與音訊產生單一影片（靜態背景 + 音樂）."""
    try:
        input_image = ffmpeg.input(png_path, loop=1)
        input_audio = ffmpeg.input(mp3_path)

        (
            ffmpeg
            .output(input_image, input_audio, output_path,
                    vcodec='libx264',
                    tune='stillimage',
                    shortest=None,
                    pix_fmt='yuv420p')
            .run(overwrite_output=True, quiet=True)
        )
        return True
    except ffmpeg.Error as e:
        print(f"[ffmpeg error] {e.stderr.decode()}")
        return False


def get_video_duration(video_path):
    """取得影片長度（秒）."""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return duration
    except:
        return 0


    
if __name__ == "__main__":

    # 迭代指定資料夾下的所有子資料夾
    folder_path = r"G:\ai_generate\Beyond a Millennium, The Mystery of Genesis Patriarchs and the Great Flood"
    for subdir in os.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir)
        if os.path.isdir(subdir_path):
            # 取出唯一 .mp3與.png
            mp3_files = [f for f in os.listdir(subdir_path) if f.endswith('.mp3')]
            png_files = [f for f in os.listdir(subdir_path) if f.endswith('.png')]

            if len(mp3_files) == 1 and len(png_files) == 1: 
                mp3_path = os.path.join(subdir_path, mp3_files[0])
                png_path = os.path.join(subdir_path, png_files[0])
                output_path = os.path.join(subdir_path, "output.mp4")

                # 產生影片
                if generate_video(mp3_path, png_path, output_path):
                    print(f"Video generated successfully: {output_path}")
                else:
                    print(f"Failed to generate video for {subdir}")