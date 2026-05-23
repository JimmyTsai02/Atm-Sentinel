# ATM Sentinel

ATM Sentinel is a Python CLI prototype for testing ATM surveillance event detection. It combines local computer vision with GPT-4o Vision to evaluate selected frames and record basic risk events.

This repository is a side-project MVP. It is not a production security system and should not be used as the sole basis for real-world financial security decisions.

## What It Does

The current flow is:

```text
Webcam / RTSP stream
-> YOLOv8 person detection
-> event trigger
-> frame snapshot
-> GPT-4o Vision risk assessment
-> terminal alert
-> SQLite event log
```

Supported in the current MVP:

- Webcam input
- RTSP input
- Local YOLOv8n person detection
- Basic lingering detection
- Basic camera occlusion detection
- Single-image testing
- Folder-based batch image testing
- GPT-4o Vision risk classification
- Rule-based policy prompt for mask / helmet ATM usage
- Terminal alert output
- Terminal-based freeze simulation
- SQLite event logging

## Current Limitations

- No Telegram or external notification integration yet
- No real ATM control API integration
- No multi-camera orchestration
- No face recognition, identity recognition, or license plate recognition
- Occlusion detection is heuristic and requires tuning per environment
- GPT-4o Vision output can vary depending on image angle, lighting, framing, and prompt wording
- The mask / helmet rule is implemented as an MVP policy prompt, not a certified compliance model

## Repository Structure

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

## Requirements

- Python 3.10+
- Webcam or RTSP camera source
- OpenAI API key

Python dependencies are listed in `requirements.txt`.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Set your OpenAI API key:

```text
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
```

Do not commit `.env`. It is ignored by `.gitignore`.

## Run Webcam / RTSP Detection

Run with the default webcam:

```powershell
python main.py
```

Specify camera index, YOLO confidence threshold, and sampling FPS:

```powershell
python main.py --camera 0 --threshold 0.5 --interval 1
```

Use an RTSP stream:

```powershell
python main.py --camera "rtsp://user:password@host/stream"
```

## Test With Images

Put local test images in `samples/`. Real test images are ignored by Git; only `samples/.gitkeep` is tracked.

Single-image test:

```powershell
python test_image.py "samples\example.jpg" --hint "Check whether a person is using an ATM while wearing a mask or helmet."
```

Batch-test all images in `samples/`:

```powershell
python test_images_folder.py
```

Use a custom folder:

```powershell
python test_images_folder.py --folder "path\to\images"
```

## Event Logs

Events are written to SQLite. By default, the database path is:

```text
atm_guard.db
```

Example query:

```sql
SELECT id, created_at, risk_level, reason, event_type, screenshot_path, actions
FROM events
ORDER BY id DESC
LIMIT 10;
```

Query events with risk level 2 or above:

```sql
SELECT id, created_at, risk_level, reason, screenshot_path
FROM events
WHERE risk_level >= 2
ORDER BY id DESC;
```

## Configuration

See `.env.example` for available settings, including:

- `OPENAI_MODEL`
- `CAMERA_INDEX`
- `RTSP_URL`
- `SAMPLE_FPS`
- `YOLO_MODEL`
- `YOLO_CONFIDENCE`
- `LINGER_THRESHOLD_SEC`
- `EVENT_COOLDOWN_SEC`
- `LOG_DIR`
- `DB_PATH`

## Privacy And Safety Notes

- Video frames are processed locally by OpenCV and YOLO.
- Event snapshots are sent to OpenAI only when an event trigger occurs.
- Snapshots and SQLite logs are stored locally by default.
- Local logs, screenshots, API keys, test images, virtual environments, and model weights are ignored by Git.

Review your own data retention, consent, and compliance requirements before using this prototype with real surveillance footage.

## License

This project is licensed under the Apache License 2.0. See `LICENSE` for details.
