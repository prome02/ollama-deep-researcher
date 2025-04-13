import requests
from io import BytesIO
from google import genai
from google.genai import types

def generate_and_send_image(api_key, model, prompt, flask_url, image_name='generated_image.jpg'):

    # 初始化 Gemini API 客戶端
    client = genai.Client(api_key=api_key)

    # 使用 API 生成圖片
    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,  # 生成一張圖片
        )
    )

    # 取得生成的圖片資料
    generated_image = response.generated_images[0].image.image_bytes
    image = BytesIO(generated_image)

    # 使用 requests 傳送圖片到 Flask 路由
    files = {'image': (image_name, image, 'image/jpeg')}
    response = requests.post(flask_url, files=files)

    return response.json()