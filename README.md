# ATM Guard CLI MVP

ATM Guard 是一個本地端 ATM 異常行為偵測 CLI MVP。系統使用 OpenCV 擷取 Webcam / RTSP 影像，透過 YOLOv8 在本地偵測人物，當觸發徘徊或遮擋事件後，將截圖交給 GPT-4o Vision 判斷風險，最後執行 terminal 警報、terminal 模擬凍結與 SQLite 事件記錄。

## 功能

- Webcam / RTSP 影像來源
- YOLOv8n 本地 person 偵測
- 徘徊計時
- 多訊號遮擋偵測：黑畫面、過亮畫面、低邊緣密度、低清晰度、低亮度變化
- GPT-4o Vision 風險判斷
- 戴安全帽或口罩操作 ATM 會判定為違規，至少觸發風險等級 2
- Function Calling 工具決策
- terminal 警報
- terminal 模擬凍結
- SQLite 事件記錄
- 截圖儲存於 `logs/`

Telegram 通知目前暫不實作，MVP 只保留本地 log。

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

## API Key 設定

請在專案根目錄建立 `.env`：

```powershell
cd "D:\side project_detect"
Copy-Item .env.example .env
notepad .env
```

在 `.env` 裡填入：

```text
OPENAI_API_KEY=你的 OpenAI API key
OPENAI_MODEL=gpt-4o
```

不要把 `.env` 提交到版本控制；本專案已在 `.gitignore` 忽略 `.env`。

## 安裝

```powershell
cd "D:\side project_detect"
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 執行 Webcam / RTSP 偵測

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

測試圖片統一放在：

```text
D:\side project_detect\samples
```

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

## GitHub 注意事項

以下檔案不應提交：

- `.env`
- `venv/`
- `logs/`
- `atm_guard.db`
- `samples/` 內的測試圖片
- `*.pt` YOLO 權重檔

請提交 `.env.example`，讓其他環境知道需要哪些設定。
