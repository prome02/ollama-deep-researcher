
# 🌍 通用 AI 翻譯提示：YouTube 劇本（中翻英）

## 🎯 使用目標
將以繁體中文撰寫的 YouTube 劇本，翻譯為美式英文旁白格式，適用於 AI TTS 語音合成與國際觀眾。兼顧文化轉譯、語氣一致與語音節奏控制。

---

## 📌 翻譯原則與語境轉換

### ✅ 1. 語境轉換重於直譯
- 中文強調意境與暗示，英文需邏輯清晰、遞進明確。
- 避免逐字翻譯中文比喻，應轉換為英文思維邏輯。

### ✅ 2. 英語語氣須符合你的人設
- 使用 first-person intellectual tone：「I believe, I often wonder, we may consider…」
- 保持思辨式敘事風格，避免 preaching 語氣。
- 優先用問句收尾引導互動：「Could this be…? What do you think?」

### ✅ 3. 宗教與哲學術語需文化對譯
| 中文原文 | 建議翻譯 |
|----------|----------|
| 末法時代 | the age of Dharma decline / moral decay |
| 修行     | spiritual practice / mental discipline |
| 因果     | cause and effect / karmic consequence |
| 退隱     | retreat into contemplation |
| 預言     | prophecy / foresight |

---

## 🔁 翻譯節奏與語音適配建議

### 🧠 節奏與結構
- 每段 Narration 控制在 250～300 詞內，利於 TTS 自然輸出。
- 句子避免過長，可使用「—」或短句強調停頓節奏。
- 可在翻譯中適度加強遞進連詞：therefore, however, perhaps, meanwhile…

### 🎙 Speak Instructions 樣式（TTS）
```text
Affect: Reflective and calm
Tone: Narrative with philosophical undertone
Emotion: Measured awe and concern
Pronunciation: Slow down for keywords like “prophecy” or “cognition”
Pause: Insert 0.5s pause before final question
```

---

## 💡 額外提示
- 翻譯經文或引用內容，優先找現成可靠英譯版本（如 CBETA, SuttaCentral, 或佛光山英譯）。
- 若無原文譯本，需用平實而莊重的語氣自行翻譯，避免誇張或扁俗語言。
- 保留觀眾互動語句於結尾（留言、訂閱、下集預告）。

---

## 📝 最終輸出格式建議
仍使用 JSON 段落格式，翻譯後每段應包含：
- `caption`
- `Narration`（翻譯後正文）
- `speak_instructions`（轉為英文 TTS 指令）
- `prompt`（圖片提示詞如需亦轉譯）

---

以上提示可作為翻譯任何以思想為導向的 YouTube 劇本之基本框架。
