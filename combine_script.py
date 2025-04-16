import os
import subprocess
import glob
from pathlib import Path
import ffmpeg
import logging

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def combine_media(folder_path):
    """
    Combines image and audio files within subfolders into one video file.
    
    This function:
    1. For each subfolder in the input folder that contains both PNG and MP3 files:
       - Combines the PNG and MP3 into an output.mp4
    2. Concatenates all output.mp4 files from subfolders based on folder creation time
    3. Creates a final output.mp4 in the root folder
    
    Args:
        folder_path (str): Path to the folder containing subfolders with media files
    """
    # Convert to absolute path
    folder_path = os.path.abspath(folder_path)
    original_dir = os.getcwd()
    os.chdir(folder_path)
    results = []

    try:
        for subdir in os.listdir('.'):
            if not os.path.isdir(subdir):
                continue

            png_files = glob.glob(os.path.join(subdir, '*.png'))
            mp3_files = glob.glob(os.path.join(subdir, '*.mp3'))

            if png_files and mp3_files:
                img_file = png_files[0]
                aud_file = mp3_files[0]
                output_file = os.path.join(subdir, 'output.mp4')

                try:
                    input_image = ffmpeg.input(img_file, loop=1)
                    input_audio = ffmpeg.input(aud_file)

                    (
                        ffmpeg.output(
                            input_image,
                            input_audio,
                            output_file,
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
                    logger.info(f"Created video for {subdir}")
                    results.append({subdir: 'Video created successfully'})
                except ffmpeg.Error as e:
                    logger.error(f"Error processing {subdir}: {str(e)}")
                    results.append({subdir: f"Error: {str(e)}"})

        subdirs = sorted(
            [d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, 'output.mp4'))],
            key=lambda x: os.path.getctime(x)
        )

        if not subdirs:
            logger.warning("No videos found to concatenate.")
            os.chdir(original_dir)
            return {"status": "No videos to concatenate"}

        concat_list_path = os.path.join(folder_path, 'concat_list.txt')
        with open(concat_list_path, 'w') as f:
            for subdir in subdirs:
                video_path = os.path.join(subdir, 'output.mp4')
                f.write(f"file '{video_path}'\n")

        try:
            final_output = os.path.join(folder_path, 'output.mp4')

            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_list_path, '-c', 'copy', final_output
            ], check=True)

            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)

            logger.info("Final video created successfully.")
            results.append({"final_output": "Video concatenated successfully"})
        except subprocess.CalledProcessError as e:
            logger.error(f"Error concatenating videos: {e}")
            results.append({"final_output": f"Error: {e}"})

    finally:
        os.chdir(original_dir)

    return results

# Example usage
if __name__ == "__main__":
    combine_media(r"G:\ai_generate\2025_en")
