import glob  # noqa: D100
import logging
import os
import subprocess
import tempfile

import ffmpeg
from tqdm import tqdm

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

    # 確保 pause_duration 足夠長，讓淡入與淡出都能完整顯示
    if fade_duration > 0 and pause_duration < fade_duration * 2:
        pause_duration = fade_duration * 2

    with tempfile.TemporaryDirectory() as tmpdir:
        final_list = []
        pause_path = None

        if pause_duration > 0:
            # 建立黑畫面過場影片
            pause_path = os.path.join(tmpdir, "pause.mp4")
            filters = []
            if fade_duration > 0:
                filters.append(f"fade=t=in:st=0:d={fade_duration}")
                filters.append(f"fade=t=out:st={pause_duration - fade_duration}:d={fade_duration}")
            fade_filter = ",".join(filters)
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=black:s=1920x1080:d=" + str(pause_duration),
                "-vf", fade_filter if fade_filter else "null",
                "-c:v", "libx264", "-t", str(pause_duration),
                pause_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)

        # 重組影片清單，穿插 pause
        for i, video in enumerate(video_paths):
            final_list.append(f"file '{os.path.abspath(video)}'")
            if i < len(video_paths) - 1 and pause_path:
                final_list.append(f"file '{os.path.abspath(pause_path)}'")

        list_txt_path = os.path.join(tmpdir, "list.txt")
        with open(list_txt_path, "w") as f:
            f.write("\n".join(final_list))

        # 執行拼接
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", list_txt_path,
            "-c", "copy", output_path
        ]
        subprocess.run(concat_cmd, check=True)

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

                    if merge_media_files(img_file, aud_file, output_file):
                        logger.info(f"Created video for {subdir}")
                        results.append({subdir: 'Video created successfully'})
                    else:
                        results.append({subdir: 'Error creating video'})

                pbar.update(1)

        if not generate_final_video:
            logger.info("Skipping final video generation as generate_final_video is False.")
            return results

        subdirs = sorted(
            [d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, 'output.mp4'))],
            key=lambda x: os.path.getctime(x)
        )

        if not subdirs:
            logger.warning("No videos found to concatenate.")
            os.chdir(original_dir)
            return {"status": "No videos to concatenate"}

        video_paths = [os.path.join(subdir, 'output.mp4') for subdir in subdirs]
        final_output = os.path.join(folder_path, 'output.mp4')

        if concatenate_video_files(video_paths, final_output):
            logger.info("Final video created successfully.")
            results.append({"final_output": "Video concatenated successfully"})
        else:
            results.append({"final_output": "Error concatenating videos"})

    finally:
        os.chdir(original_dir)

    return results

def generate_one_second_video(output_path: str, color: str = "black"):
    """Generates a one-second-long MP4 video with a specified background color and silent audio.

    Args:
        output_path (str): Path to save the generated MP4 file.
        color (str): Background color of the video (default is "black").

    Returns:
        bool: True if the video is generated successfully, False otherwise.
    """  # noqa: D401
    try:
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', '1',
            '-vf', f'color={color}:size=1920x1080:rate=30', '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-c:a', 'aac', output_path
        ], check=True)
        logger.info(f"One-second video with color '{color}' generated at {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error generating one-second video: {e}")
        return False


if __name__ == "__main__":
    concatenate_video_files(
    ["test1.mp4", "test2.mp4"],
    "output.mp4",
    {
        "pause_duration": 2,
        "fade_duration": 1
    }
)


