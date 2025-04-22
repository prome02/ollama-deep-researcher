from combine_script import combine_media

def run_combine_media():
    folder_path = "test_folder"  # 替換為實際的資料夾路徑
    generate_final_video = False
    audio_consistency = True

    # 呼叫 combine_media 函數
    results = combine_media(folder_path, generate_final_video=generate_final_video, audio_consistency=audio_consistency)

    # 列印結果
    for result in results:
        print(result)

if __name__ == "__main__":
    run_combine_media()