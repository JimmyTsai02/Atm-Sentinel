# ATM Guard CLI MVP

ATM Guard 是一個本地端 Python CLI side project，用來測試 ATM 監控影像的異常事件判斷流程。

目前版本是 MVP，不是正式監控產品。它主要用來驗證以下流程是否可行：

```text
Webcam / RTSP 影像
→ YOLOv8 偵測人物
→ 觸發事件時截圖
→ GPT-4o Vision 判斷風險
→ terminal 顯示警示
→ SQLite 記錄事件
```

## 目前支援

- Webcam 或 RTSP 影像來源
- YOLOv8n 本地 person 偵測
- 人物停留時間計算
- 簡易鏡頭遮擋偵測
- 單張圖片測試
- 資料夾批次圖片測試
- GPT-4o Vision 風險判斷
- 戴口罩或安全帽操作 ATM 時，依目前規則判定為風險等級 2
- terminal 警示輸出
- terminal 模擬凍結
- SQLite 事件記錄

## 目前限制

- 尚未串接 Telegram 通知
- 尚未支援真實 ATM 控制 API
- 尚未支援多路攝影機同時監控
- 尚未實作人臉辨識、身分識別或車牌辨識
- 鏡頭遮擋與違規判斷仍屬 MVP 規則，需要依實際場景調參
- GPT-4o 判斷結果可能受圖片角度、光線、遮擋與 prompt 影響

## 專案結構

```text
.
├── main.py
├── config.py
├── detector.py
├── llm_judge.py
├── database.py
├── test_image.py
├── test_images_folder.py
├── requirements.txt
├── .env.example
├── tools/
│   ├── alert.py
│   └── freeze.py
└── samples/
```

## API Key

請在專案根目錄建立 `.env`：

```powershell
Copy-Item .env.example .env
notepad .env
```

在 `.env` 裡填入：

```text
OPENAI_API_KEY=你的 OpenAI API key
OPENAI_MODEL=gpt-4o
```

`.env` 已被 `.gitignore` 忽略，請不要提交真實 API key。

## 安裝

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

第一次使用 YOLOv8n 時，Ultralytics 會下載 `yolov8n.pt` 權重檔。此檔案已被 `.gitignore` 忽略。

## 執行 Webcam / RTSP

使用預設 Webcam：

```powershell
python main.py
```

指定攝影機、YOLO threshold、採樣 FPS：

```powershell
python main.py --camera 0 --threshold 0.5 --interval 1
```

使用 RTSP：

```powershell
python main.py --camera "rtsp://user:password@host/stream"
```

## 圖片測試

測試圖片可放在 `samples/`。實際圖片不會提交到 GitHub，資料夾內只保留 `.gitkeep`。

單張圖片測試：

```powershell
python test_image.py "samples\test02.jpg" --hint "請檢查是否有人戴安全帽或口罩操作 ATM"
```

批次測試整個資料夾：

```powershell
python test_images_folder.py
```

指定其他資料夾：

```powershell
python test_images_folder.py --folder "samples"
```

## SQLite 查詢

查看最近 10 筆事件：

```sql
SELECT id, created_at, risk_level, reason, event_type, screenshot_path, actions
FROM events
ORDER BY id DESC
LIMIT 10;
```

查看風險等級 2 以上：

```sql
SELECT id, created_at, risk_level, reason, screenshot_path
FROM events
WHERE risk_level >= 2
ORDER BY id DESC;
```

## 不提交到 GitHub 的檔案

- `.env`
- `venv/`
- `logs/`
- `atm_guard.db`
- `samples/` 內的測試圖片
- `*.pt` YOLO 權重檔
- `ATM_Guard_PRD.docx`
