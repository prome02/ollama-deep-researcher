import requests

# 從 HTTP 請求節點接收的 JSON 參數


def main2(jobj: str, api_key: str) -> dict:
    # 生成 TTS 請求
    tts_url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = jobj

    # 請求 TTS 並獲取 .mp3 二進制數據
    response = requests.post(tts_url, headers=headers, json=data)
    response.raise_for_status()  # 檢查錯誤

    # 調用本地保存端點
    save_url = "http://192.168.50.21:9125/save_mp3"
    files = {'file': ('output.mp3', response.content, 'audio/mpeg')}
    save_response = requests.post(save_url, files=files)

    # 返回結果
    return {
        "result": "MP3 保存成功" if save_response.ok else "保存失敗"
        
    }
    
    import requests
def main(jobj: str, url: str) -> dict:
    # 調用本地保存端點，直接傳遞 jobj
    save_url = f"{url}/save_mp3"
    headers = {"Content-Type": "application/json"}
    
    # 發送 JSON 到 /save_mp3
    save_response = requests.post(save_url, headers=headers, json={"jobj": jobj})

    # 返回結果
    return {
        "result": "MP3 保存成功" if save_response.ok else "保存失敗",
    }
    
if __name__ == '__main__':
    import json
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("找不到 OPENAI_API_KEY，請確認 .env 檔")
    jobj = {  "model":"gpt-4o-mini-tts",
            "voice":"alloy",
            "input":"""Welcome, viewers. Our world is full of mysteries, and few are as captivating as the Pyramids of Giza—massive structures that have stood for thousands of years
            """,
            "instructions":"以神秘且莊嚴的語調開場，語速平穩，聲音富有磁性和深度，表達對古老謎題的敬畏和好奇，適當在關鍵處停頓以增強效果"
            }
    
    resp= main(jobj, "http://192.168.50.20:9125")
    print(resp)

