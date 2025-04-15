import os
import json

def split_json_by_language(file_path):
    # 獲取檔案名稱（不含副檔名）和路徑
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join(os.path.dirname(file_path), base_name)
    
    # 建立輸出資料夾
    os.makedirs(output_dir, exist_ok=True)
    
    # 載入 JSON 檔案
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # 英文版和中文版的模板
    data_en = {"language": "en"}
    data_zh = {"language": "zh"}
    
    # 處理 title
    data_en["title"] = data["title"]["en"]
    data_zh["title"] = data["title"]["zh"]
    
    # 保留其他屬性（如 music）
    data_en["music"] = data["music"]
    data_zh["music"] = data["music"]
    
    # 處理 content
    data_en["content"] = []
    data_zh["content"] = []
    
    for item in data["content"]:
        # 英文版
        item_en = {
            "caption": item["caption"]["en"],
            "description": item["description"],
            "Narration": item["Narration"]["en"],
            "speak_instructions": item["speak_instructions"],
            "prompt": item["prompt"]
        }
        data_en["content"].append(item_en)
        
        # 中文版
        item_zh = {
            "caption": item["caption"]["zh"],
            "description": item["description"],
            "Narration": item["Narration"]["zh"],
            "speak_instructions": item["speak_instructions"],
            "prompt": item["prompt"]
        }
        data_zh["content"].append(item_zh)
    
    # 處理 resource 和 note
    data_en["resource"] = data["resource"]
    data_zh["resource"] = data["resource"]
    
    data_en["note"] = data["note"]
    data_zh["note"] = data["note"]
    
    # 輸出檔案路徑
    output_file_en = os.path.join(output_dir, f"{base_name}_en.json")
    output_file_zh = os.path.join(output_dir, f"{base_name}_zh.json")
    
    # 寫入英文版 JSON
    with open(output_file_en, "w", encoding="utf-8") as file:
        json.dump(data_en, file, ensure_ascii=False, indent=4)
    
    # 寫入中文版 JSON
    with open(output_file_zh, "w", encoding="utf-8") as file:
        json.dump(data_zh, file, ensure_ascii=False, indent=4)
    
    print(f"輸出完成！檔案已儲存於資料夾：{output_dir}")

# 使用範例
file_path = r"""d:\downloadProj\ollama-deep-researcher\content\【震撼揭秘】2025年吉薩金字塔地下巨大結構發現.json"""
split_json_by_language(file_path)