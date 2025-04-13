import requests

# 從 HTTP 請求節點接收的 JSON 參數


def main(jobj: str, api_key: str) -> dict:
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
