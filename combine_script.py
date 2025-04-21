import glob  # noqa: D100
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import ffmpeg
from tqdm import tqdm

# Initialize logger
logger = logging.getLogger(__name__)

def generate_pause_video(pause_duration, fade_duration, resolution, frame_rate, pix_fmt):
    cache_dir = Path("./pause_cache")
    cache_dir.mkdir(exist_ok=True)
    pause_filename = f"pause_{pause_duration}s_fade{fade_duration}s.mp4"
    pause_path = cache_dir / pause_filename
    
    # 清除已有的快取文件（測試期間）
    if pause_path.exists():
        pause_path.unlink()
    
    # 建立淡入淡出濾鏡
    filters = []
    if fade_duration > 0:
        filters.append(f"fade=t=in:st=0:d={fade_duration}")
        filters.append(f"fade=t=out:st={pause_duration - fade_duration}:d={fade_duration}")
    fade_filter = ",".join(filters)
    
    # 使用 ffmpeg 產生 pause.mp4（含靜音）
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:s={resolution}:r={frame_rate}:d={pause_duration}",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-vf", fade_filter if fade_filter else "null",
        "-shortest",
        "-c:v", "libx264", "-pix_fmt", pix_fmt,
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(pause_duration),
        str(pause_path)
    ]
    
    print(f"Generating pause video with command: {' '.join(ffmpeg_cmd)}")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error generating pause video: {result.stderr}")
        return None
    
    # 驗證生成的影片
    check_cmd = ["ffprobe", "-v", "error", "-show_format", "-show_streams", str(pause_path)]
    check_result = subprocess.run(check_cmd, capture_output=True, text=True)
    
    print(f"Pause video info: {check_result.stdout}")
    
    return str(pause_path)

def get_video_format(path):
    """Retrieve video format details using ffprobe.

    Args:
        path (str): Path to the video file.

    Returns:
        dict: A dictionary containing resolution, pixel format, and frame rate of the video.
    """
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,pix_fmt",
        "-of", "json", path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(result.stdout)['streams'][0]

    width = info['width']
    height = info['height']
    pix_fmt = info['pix_fmt']
    framerate_str = info['r_frame_rate']
    framerate = eval(framerate_str)  # r_frame_rate is like "30/1"

    return {
        "resolution": f"{width}x{height}",
        "pix_fmt": pix_fmt,
        "framerate": framerate
    }

def merge_media_files(image_path: str, audio_path: str, output_path: str):
    """Merges an image file and an audio file into a single MP4 video.

    Args:
        image_path (str): Path to the image file.
        audio_path (str): Path to the audio file.
        output_path (str): Path to save the output MP4 file.

    Returns:
        bool: True if the merge is successful, False otherwise.
    """  # noqa: D401
    try:
        input_image = ffmpeg.input(image_path, loop=1)
        input_audio = ffmpeg.input(audio_path)

        (
            ffmpeg.output(
                input_image,
                input_audio,
                output_path,
                vf="scale=1920:1046",
                vcodec='libx264',
                tune='stillimage',
                acodec='aac',
                audio_bitrate='192k',
                pix_fmt='yuv420p',
                shortest=None
            )
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except ffmpeg.Error as e:
        logger.error(f"Error merging media files: {str(e)}")
        return False

def concatenate_video_files(video_paths: list, output_path: str, ext_setting: dict = None):  # noqa: D103
    if ext_setting is None:
        ext_setting = {}

    pause_duration = ext_setting.get("pause_duration", 0)
    fade_duration = ext_setting.get("fade_duration", 0)

    print(f"Starting video concatenation with {len(video_paths)} videos")
    print(f"Pause duration: {pause_duration}s, Fade duration: {fade_duration}s")

    # 檢查所有影片檔案的格式
    for i, video_path in enumerate(video_paths):
        print(f"Checking video {i+1}: {video_path}")
        video_info = get_video_format(video_path)
        print(f"  Resolution: {video_info['resolution']}")
        print(f"  Framerate: {video_info['framerate']}")
        print(f"  Pixel format: {video_info['pix_fmt']}")

    # 建立暫存目錄
    with tempfile.TemporaryDirectory() as tmpdir:
        concat_list_path = os.path.join(tmpdir, "concat_list.txt")
        
        pause_path = None
        if pause_duration > 0:
            # 取得第一支影片格式資訊
            first_video = video_paths[0]
            video_info = get_video_format(first_video)
            resolution = video_info["resolution"]
            frame_rate = video_info["framerate"]
            pix_fmt = video_info["pix_fmt"]
            
            print(f"Creating pause video with format: {resolution}, {frame_rate} fps, {pix_fmt}")
            
            # 建立或重用 pause.mp4
            pause_path = generate_pause_video(
                pause_duration, fade_duration, resolution, frame_rate, pix_fmt
            )
            
            if pause_path:
                print(f"Pause video created successfully: {pause_path}")
                pause_info = get_video_format(pause_path)
                print(f"  Resolution: {pause_info['resolution']}")
                print(f"  Framerate: {pause_info['framerate']}")
                print(f"  Pixel format: {pause_info['pix_fmt']}")
            else:
                print("Failed to create pause video!")
                return False

        # 建立 concat list
        with open(concat_list_path, "w") as f:
            for i, path in enumerate(video_paths):
                f.write(f"file '{os.path.abspath(path)}'\n")
                if pause_duration > 0 and i < len(video_paths) - 1 and pause_path:
                    f.write(f"file '{os.path.abspath(pause_path)}'\n")
        
        print(f"Concat list created at: {concat_list_path}")
        
        # 顯示 concat list 內容
        with open(concat_list_path, "r") as f:
            print("Concat list content:")
            print(f.read())
        
        # 使用 concat 模式合併
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list_path,
            "-fflags", "+genpts",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-async", "1",
            output_path
        ]
        
        print(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error concatenating videos: {result.stderr}")
            return False
        else:
            print(f"Videos successfully concatenated to: {output_path}")
            
            # 檢查輸出檔案
            output_info = get_video_format(output_path)
            print(f"Output video information:")
            print(f"  Resolution: {output_info['resolution']}")
            print(f"  Framerate: {output_info['framerate']}")
            print(f"  Pixel format: {output_info['pix_fmt']}")
            
            return True

def combine_media(folder_path, generate_final_video: bool = False):
    """Combines image and audio files within subfolders into one video file.
    
    This function:
    1. For each subfolder in the input folder that contains both PNG and MP3 files:
       - Combines the PNG and MP3 into an output.mp4
    2. Optionally concatenates all output.mp4 files from subfolders based on folder creation time
    3. Creates a final output.mp4 in the root folder if generate_final_video is True
    
    Args:
        folder_path (str): Path to the folder containing subfolders with media files
        generate_final_video (bool): Whether to generate the final concatenated video
    """  # noqa: D401
    # Convert to absolute path
    folder_path = os.path.abspath(folder_path)
    original_dir = os.getcwd()
    os.chdir(folder_path)
    results = []

    try:
        subdirs = [d for d in os.listdir('.') if os.path.isdir(d)]
        total_subdirs = len(subdirs)

        with tqdm(total=total_subdirs, desc="Processing folders", unit="folder") as pbar:
            try:
                for subdir in subdirs:
                    if not os.path.isdir(subdir):
                        pbar.update(1)
                        continue

                    png_files = glob.glob(os.path.join(subdir, '*.png'))
                    mp3_files = glob.glob(os.path.join(subdir, '*.mp3'))

                    if png_files and mp3_files:
                        img_file = png_files[0]
                        aud_file = mp3_files[0]
                        output_file = os.path.join(subdir, 'output.mp4')

                        # Skip if output_file already exists
                        if os.path.exists(output_file):
                            logger.info(f"Skipping {subdir} as output file already exists.")
                            results.append({subdir: 'Output file already exists'})
                            pbar.update(1)
                            continue

                        if merge_media_files(img_file, aud_file, output_file):
                            logger.info(f"Created video for {subdir}")
                            results.append({subdir: 'Video created successfully'})
                        else:
                            results.append({subdir: 'Error creating video'})

                    pbar.update(1)
            finally:
                pbar.close()  # Ensure the progress bar is closed even if an error occurs

        # if not generate_final_video:
        #     logger.info("Skipping final video generation as generate_final_video is False.")
        #     return results

        # subdirs = sorted(
        #     [d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, 'output.mp4'))],
        #     key=lambda x: os.path.getctime(x)
        # )

        # if not subdirs:
        #     logger.warning("No videos found to concatenate.")
        #     os.chdir(original_dir)
        #     return {"status": "No videos to concatenate"}

        # video_paths = [os.path.join(subdir, 'output.mp4') for subdir in subdirs]
        # final_output = os.path.join(folder_path, 'output.mp4')

        # if concatenate_video_files(video_paths, final_output, {
        #     "pause_duration": 2,
        #     "fade_duration": 1
        # }):
        #     logger.info("Final video created successfully.")
        #     results.append({"final_output": "Video concatenated successfully"})
        # else:
        #     results.append({"final_output": "Error concatenating videos"})

    finally:
        os.chdir(original_dir)

    return results

def test_concatenation(video_files, output_path, pause_duration=0, fade_duration=0):
    """測試不同設定的影片合併效果."""
    print(f"\n{'='*50}")
    print(f"Testing with pause_duration={pause_duration}, fade_duration={fade_duration}")
    print(f"{'='*50}")
    
    # 先測試不加入 pause
    if pause_duration > 0:
        print("\nStep 1: Testing without pause first")
        no_pause_output = f"{output_path.rsplit('.', 1)[0]}_no_pause.mp4"
        concatenate_video_files(video_files, no_pause_output, {"pause_duration": 0})
        
        # 檢查輸出
        if os.path.exists(no_pause_output):
            print(f"No pause test successful: {no_pause_output}")
        else:
            print(f"No pause test failed!")
    
    # 現在測試加入 pause
    print("\nStep 2: Testing with configured pause")
    with_pause_output = output_path
    result = concatenate_video_files(video_files, with_pause_output, {
        "pause_duration": pause_duration,
        "fade_duration": fade_duration
    })
    
    if result:
        print(f"With pause test successful: {with_pause_output}")
    else:
        print(f"With pause test failed!")
    
    print(f"\nTest completed. Please check the results manually.")


if __name__ == "__main__":
    
    test_videos = ["G:/ai_generate/The_Great_Underground_Discovery_Massive_Structures_Beneath_the_Giza_Pyramids/Academic_Controversy_Skepticism_and_Debate/output.mp4", 
     "G:/ai_generate/The_Great_Underground_Discovery_Massive_Structures_Beneath_the_Giza_Pyramids/Background_The_Giza_Pyramid_Complex/output.mp4"]
    
    # 測試不同的 pause 設定
    test_concatenation(test_videos, "output_test1.mp4", pause_duration=2, fade_duration=0.5)
    test_concatenation(test_videos, "output_test2.mp4", pause_duration=3, fade_duration=1)
#     concatenate_video_files(
#     ["G:/ai_generate/The_Great_Underground_Discovery_Massive_Structures_Beneath_the_Giza_Pyramids/Academic_Controversy_Skepticism_and_Debate/output.mp4", 
#      "G:/ai_generate/The_Great_Underground_Discovery_Massive_Structures_Beneath_the_Giza_Pyramids/Background_The_Giza_Pyramid_Complex/output.mp4"],
#     "f:/download/output.mp4",
#     {
#         "pause_duration": 4,
#         "fade_duration": 3
#     }
# )


