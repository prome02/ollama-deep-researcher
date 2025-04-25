"""Utility functions for generating images, videos, and managing files.

This module provides:
- Functions to generate images using Google GenAI.
- Video generation using static images and audio.
- File renaming based on creation time.
"""

import os
import json
import requests
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


def rename_output_files_by_creation_time(folder_path):  # noqa: D103
    # Get all subdirectories in the folder
    subdirs = [os.path.join(folder_path, d) for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]

    # Sort subdirectories by creation time (earliest first)
    subdirs.sort(key=lambda d: os.path.getctime(d))

    # Iterate through sorted subdirectories and rename output.mp4 files
    for index, subdir in enumerate(subdirs, start=1):
        output_file_path = os.path.join(subdir, "output.mp4")
        if os.path.exists(output_file_path):
            new_name = f"{str(index).zfill(2)}_output.mp4"
            new_file_path = os.path.join(subdir, new_name)
            os.rename(output_file_path, new_file_path)
            print(f"Renamed {output_file_path} to {new_file_path}")


def generate_audio_file(jobj, tts_url, logger= None):
    """Call OpenAI API to generate an audio file."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        if logger :
            logger.info("Sending TTS request to OpenAI API")
            logger.info(json.dumps(jobj, indent=2, ensure_ascii=False))
        tts_response = requests.post(tts_url, headers=headers, json=jobj)
        tts_response.raise_for_status()
        return tts_response.content
    except requests.exceptions.RequestException as e:
        if logger :
            logger.error(f"TTS request failed: {str(e)}")
        raise


if __name__ == "__main__":

    # 迭代指定資料夾下的所有子資料夾
    folder_path = r"G:\ai_generate\Cycles_of_Civilization_Have_We_Been_Here_Before"
    # for subdir in os.listdir(folder_path):
    #     subdir_path = os.path.join(folder_path, subdir)
    #     if os.path.isdir(subdir_path):
    #         # 取出唯一 .mp3與.png
    #         mp3_files = [f for f in os.listdir(subdir_path) if f.endswith('.mp3')]
    #         png_files = [f for f in os.listdir(subdir_path) if f.endswith('.png')]

    #         if len(mp3_files) == 1 and len(png_files) == 1: 
    #             mp3_path = os.path.join(subdir_path, mp3_files[0])
    #             png_path = os.path.join(subdir_path, png_files[0])
    #             output_path = os.path.join(subdir_path, "output.mp4")

    #             # 產生影片
    #             if generate_video(mp3_path, png_path, output_path):
    #                 print(f"Video generated successfully: {output_path}")
    #             else:
    #                 print(f"Failed to generate video for {subdir}")

    # Rename output files by creation time
    # rename_output_files_by_creation_time(folder_path)
    tts_payload = {
                "model": "gpt-4o-mini-tts",
                "voice": "onyx",
                "input": "If you’ve seen my other video on the latest findings beneath the Giza Plateau, you’ll know this: in March 2025, a team of Italian and British researchers shook the academic world with their discovery. Using advanced radar, they detected unusual subterranean structures lying 1.2 kilometers deep and stretching across nearly 2 kilometers of terrain beneath the pyramids. Among the findings were vertical shafts and spiraling corridors—features reminiscent of the mythical Hall of Amenti from ancient Egyptian lore, where souls faced judgment. While these structures haven’t been physically excavated yet, and their age and purpose remain uncertain, the possibility is tantalizing: could these be messages deliberately left by an earlier civilization—for us?",
                "instructions":"Affect: Reflective and analytical. Tone: Narrative with philosophical undertone. Emotion: Thoughtful concern and curiosity. Pronunciation: Emphasize key cultural or philosophical terms. Pause: Insert 0.5s pause at the end of each segment to allow reflection and smooth transition."
            }
    tts_url = "https://api.openai.com/v1/audio/speech"
    
    #surrond try  catch
    try:
        audio_content = generate_audio_file(jobj= tts_payload, tts_url=tts_url)
        with open(r"G:\ai_generate\The_Truth_Behind_Doomsday_Prophecies_From_Ancient_Wisdom_to_the_Age_of_AI\03Underground_Chambers_and_Ancient_Warnings\03If_youve_seen_my_other_video_on_the_latest_findin.mp3", "wb") as f:
            f.write(audio_content)
    except Exception as e:
        print(f"Error: {e}")  # noqa: T201
