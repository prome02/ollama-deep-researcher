def main(depth: int, method: str) -> dict:
    prompts = {
        "youtube": {
            "search": """
        你是有經驗的youtube旁白作者。 為了寫一篇旁白正在調查以下主題(topic)。
調查方向著重在提及事件的發生過程，包括 相關的 人物、事件、時間點、地點、特殊或關鍵物品。
其次是主題廣泛的第三人評論、專家意見、不同觀點、不確定性等等，作為旁白反思段落的素材。
        """,
            "writting": """
        你是一位具有豐富經驗的 YouTube 旁白撰稿人，擅長將複雜的資訊轉化為吸引觀眾的敘事內容。請根據以下 <調查結果>，撰寫一篇適合用於 YouTube 影片的繁體中文的旁白稿。旁白內容需具備資訊性與故事性，並按照以下四段結構編排：
背景介紹：說明這項調查的起因與背景，簡介事件所處的社會、歷史或文化脈絡。
事件詳述：深入描述調查中揭露的重要事件，包含關鍵人物、地點、時間軸、事件經過、涉及物品等資訊，強調其發展脈絡與重要細節。
觀點與反思：引入第三方評論、專家分析、不同立場觀點，探討此事件的意義、可能的爭議、不確定性或尚待釐清的問題。
總結結論：統整整體資訊，給出對觀眾有啟發性的結語，並可點出值得關注的後續發展或延伸思考方向。

請根據調查資料，幫我：
撰寫一個吸引人的影片標題（Title）, 參考 <主題>，產出完整的 YouTube 旁白稿（長文本）
        """,
        },
        "research": {
            "search": """
        You are a research agent investigating the following topic.
        """,
            "writting": """
            ** 要以繁體中文輸出。
** Based on the investigation results, create a comprehensive analysis of the topic.\nProvide important insights, conclusions, and remaining uncertainties. Cite sources where appropriate. This analysis should be very comprehensive and detailed. It is expected to be a long text
            """,
        },
    }
    depth = depth or 3
    array = list(range(depth))
    return {
        "array": array, 
        "depth": depth,
        "style": prompts[method]["search"],
        "writting":prompts[method]["writting"]
        }
