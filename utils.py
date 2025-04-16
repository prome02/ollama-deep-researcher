import os
import shutil
from io import BytesIO

import ffmpeg
import requests
from google.genai import Client, types
from PIL import Image
from werkzeug.utils import secure_filename


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

# def process_folder_logic(folder_path, callback=None):
    if not folder_path or not os.path.exists(folder_path):
        return {'error': 'Invalid folder path'}, 400

    subfolders = [
        os.path.join(folder_path, name) for name in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, name))
    ]
    subfolders.sort(key=os.path.getctime)

    video_files = []
    durations = []
    for idx, sub in enumerate(subfolders):
        mp3_list = [f for f in os.listdir(sub) if f.endswith('.mp3')]
        png_list = [f for f in os.listdir(sub) if f.endswith('.png')]

        if len(mp3_list) != 1 or len(png_list) != 1:
            print(f"Skipped: {sub} does not contain exactly one .mp3 and one .png")
            continue

        mp3_path = os.path.join(sub, mp3_list[0])
        png_path = os.path.join(sub, png_list[0])
        video_output = os.path.join(sub, 'video.mp4')

        success = generate_video(mp3_path, png_path, video_output)
        if success:
            duration = get_video_duration(video_output)
            if duration > 0:
                video_files.append(video_output)
                durations.append(duration)
                if callback:
                    callback(f"[{idx+1}/{len(subfolders)}] Created: {video_output}")
            else:
                print(f"Invalid duration for: {video_output}")
        else:
            print(f"Failed to generate video for: {sub}")

    if len(video_files) < 2:
        return {'error': 'At least two valid videos required for transition merge.'}, 400

    try:
        # 產生轉場影片
        inputs = [ffmpeg.input(v) for v in video_files]
        fade_duration = 1  # 1 秒淡入淡出

        stream = inputs[0]
        current_time = durations[0] - fade_duration

        for i in range(1, len(inputs)):
            stream = ffmpeg.filter([stream, inputs[i]], 'xfade',
                                   transition='fade',
                                   duration=fade_duration,
                                   offset=current_time)
            current_time += durations[i] - fade_duration

        final_output = os.path.join(folder_path, 'final_output.mp4')
        (
            ffmpeg
            .output(stream, final_output, vcodec='libx264', pix_fmt='yuv420p')
            .run(overwrite_output=True, quiet=True)
        )

        if callback:
            callback("✅ Final merge completed.")

        return {'message': 'Video processing completed with transitions', 'output': final_output}, 200

    except ffmpeg.Error as e:
        return {'error': 'Failed to merge videos with transition', 'details': e.stderr.decode()}, 500

def replace_png_files(batch_dir, target_base_dir):
    """Iterate through .png files in batch_dir and replace matching files in target_base_dir subfolders."""
    if not os.path.exists(batch_dir):
        return {"error": "Batch directory does not exist"}

    if not os.path.exists(target_base_dir):
        return {"error": "Target base directory does not exist"}

    # Iterate through .png files in batch_dir
    for file_name in os.listdir(batch_dir):
        if file_name.endswith('.png'):
            batch_file_path = os.path.join(batch_dir, file_name)

            # Search for matching files in target_base_dir subfolders
            for root, _, files in os.walk(target_base_dir):
                if file_name in files:
                    target_file_path = os.path.join(root, file_name)

                    # Replace the file
                    try:
                        shutil.copy2(batch_file_path, target_file_path)
                        print(f"Replaced: {target_file_path}")
                    except Exception as e:
                        print(f"Failed to replace {target_file_path}: {e}")

    return {"message": "Replacement process completed"}

    
if __name__ == "__main__":
    batch_dir = "G:\\batch\\"
    target_base_dir = "G:\\ai_generate\\The_Great_Underground_Discovery_Massive_Structures_Beneath_the_Giza_Pyramids\\"
    # result = replace_png_files(batch_dir, target_base_dir)
