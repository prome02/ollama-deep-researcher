import glob
import logging
import os
import subprocess
from pathlib import Path

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

def concatenate_video_files(video_paths: list, output_path: str):
    """
    Concatenates multiple MP4 video files into a single MP4 video.

    Args:
        video_paths (list): List of paths to MP4 video files to concatenate.
        output_path (str): Path to save the concatenated MP4 file.

    Returns:
        bool: True if the concatenation is successful, False otherwise.
    """  # noqa: D212
    concat_list_path = 'concat_list.txt'
    try:
        with open(concat_list_path, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")

        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list_path, '-c', 'copy', output_path
        ], check=True)

        os.remove(concat_list_path)
        return True
    except (subprocess.CalledProcessError, OSError) as e:
        logger.error(f"Error concatenating video files: {e}")
        return False

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

# Example usage
if __name__ == "__main__":
    combine_media(r"G:\ai_generate\2025_en")
