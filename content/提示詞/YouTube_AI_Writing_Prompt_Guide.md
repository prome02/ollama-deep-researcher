
# ✅ 通用 AI 寫作提示：YouTube 劇本（旁白）

## 🎯 撰寫目標
撰寫一篇約 20 分鐘長的 YouTube 劇本旁白，用於影片配音與畫面引導。文章語氣為 **理性、敘事式探索**，適度懷疑與哲思，**保留觀眾互動與懸念引導**。每段控制在 300 詞內。最終格式為 JSON 段落物件。

---

## 🧱 劇本結構建議（段落模版）

1. **開場段落**：營造場景或設問引導，設下主題「鉤子」與懸念。
2. **主敘述段落**：描繪事件、提出觀點、引用資料、搭配場景。
3. **引導思考段落**：反思前述現象、揭露矛盾、建立多重觀點。
4. **深化段落**：引用歷史、預言、經文、哲學做對照。
5. **結語段落**：統整主題、設下延伸問題或預告下一集。

---

## 🔁 語氣與結構指導語

### 🎙 語氣設定
- 語氣：理性中帶懷疑、神秘但有邏輯、探索式語氣
- 主詞使用：以「我」為主體輸出思想，也可搭配「我們」「你是否也…」
- 結尾設計：每段可加入懸念或問題，引導觀眾留言、訂閱、思考

### 🧩 懸念設計句型
- “這背後是否隱藏著某種更深的規律？”
- “是巧合，還是我們沒看懂的模式？”
- “這一切，真的是進步嗎？”
- “你認同這樣的解釋嗎？還是有更合理的看法？”

---

## 🛠 JSON 段落格式指引（每段）

```json
{
  "No.": "段落編號",
  "caption": "段落小標",
  "UUID": "唯一識別碼",
  "timestamp": "時間碼",
  "voice_actor": "語音角色（可選）",
  "Narration": "旁白正文，每段不超過 300 詞",
  "speak_instructions": "語音情緒與節奏提示，TTS 專用",
  "prompt": "生成圖像提示詞"
}
```

---

## 🎧 語音提示（Speak Instructions）模板

- Affect: Concluding yet opening new horizons  
- Tone: Reflective with forward momentum  
- Emotion: Satisfied curiosity with invitation for more  
- Pronunciation: Emphasize keywords, clear call to action  
- Pause: Insert 0.5s pause before key questions or ending lines

---

## 🖼 圖像 Prompt Style 建議

- 統一風格：cinematic / philosophical / documentary / symbolic
- 可加元素：
  - 時代背景（ancient Egypt, digital age, future dystopia）
  - 情緒主題（mystery, revelation, contrast）
  - 色調建議（gold-blue, parchment, shadow & light）

---

## ✨ 資料參考比重建議
- 英文資料 >50%（國際主流來源與最新觀點）
- 中文資料（輔助文化脈絡）


---

## 📌 額外提醒
- 避免過度「你應該…」式語句，保持中立探問
- 中式比喻（如因果、輪迴）要適度轉換為英文思維邏輯
- 保留多元觀點，但建構清晰論述主軸

---

## 標準json模板
{
  "language": "en",
  "title": "Episode Title Placeholder",
  "introduction": "This episode explores...",
  "hashtag": ["#civilization", "#AI", "#prophecy"],
  "prompt_style": "cinematic symbolic realism",
  "content": [
    {
      前述 'JSON 段落格式指引'
      },
    // repeat for No. 02 to ...
  ],
  "resource": ["資料來源1",
        "資料來源2",
        ...
        ],
  "note": "其他注意事項, 非必要。"
}
