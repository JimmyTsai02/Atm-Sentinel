from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2

from config import Settings, load_settings
from database import EventDatabase, EventRecord
from detector import ATMDetector, DetectionResult
from llm_judge import ATMVisionJudge, JudgeResult
from tools import freeze_terminal, trigger_alert


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ATM Guard CLI MVP")
    parser.add_argument("--camera", help="Webcam device index 或 RTSP URL")
    parser.add_argument("--threshold", type=float, help="YOLO confidence threshold")
    parser.add_argument("--interval", type=int, help="每秒採樣幀數")
    return parser.parse_args()


def apply_cli_overrides(settings: Settings, args: argparse.Namespace) -> Settings:
    values = settings.__dict__.copy()
    if args.camera:
        if args.camera.isdigit():
            values["camera_index"] = int(args.camera)
            values["rtsp_url"] = ""
        else:
            values["rtsp_url"] = args.camera
    if args.threshold is not None:
        values["yolo_confidence"] = args.threshold
    if args.interval is not None:
        values["sample_fps"] = max(1, args.interval)
    return Settings(**values)


def save_screenshot(frame, log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = log_dir / f"event_{timestamp}.jpg"
    cv2.imwrite(str(path), frame)
    return path


def execute_actions(
    judge_result: JudgeResult,
    db: EventDatabase,
    detection: DetectionResult,
    screenshot_path: Path,
) -> int:
    if "trigger_alert" in judge_result.actions:
        trigger_alert(judge_result.risk_level, judge_result.reason)
    if "freeze_terminal" in judge_result.actions:
        freeze_terminal(judge_result.risk_level, judge_result.reason)

    return db.log_event(
        EventRecord(
            risk_level=judge_result.risk_level,
            reason=judge_result.reason,
            event_type=detection.event_type or "unknown",
            screenshot_path=str(screenshot_path),
            actions=json.dumps(judge_result.actions, ensure_ascii=False),
        )
    )


def open_camera(settings: Settings) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(settings.camera_source)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.frame_width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.frame_height)
    if not capture.isOpened():
        raise RuntimeError(f"無法開啟影像來源：{settings.camera_source}")
    return capture


def run() -> None:
    args = parse_args()
    settings = apply_cli_overrides(load_settings(), args)
    db = EventDatabase(settings.db_path)
    detector = ATMDetector(
        model_path=settings.yolo_model,
        confidence=settings.yolo_confidence,
        linger_threshold_sec=settings.linger_threshold_sec,
        event_cooldown_sec=settings.event_cooldown_sec,
        occlusion_dark_ratio=settings.occlusion_dark_ratio,
        occlusion_bright_ratio=settings.occlusion_bright_ratio,
        occlusion_edge_density=settings.occlusion_edge_density,
        occlusion_blur_variance=settings.occlusion_blur_variance,
        occlusion_stddev=settings.occlusion_stddev,
        occlusion_consecutive_frames=settings.occlusion_consecutive_frames,
    )
    judge = ATMVisionJudge(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        max_retries=settings.openai_max_retries,
    )

    capture = open_camera(settings)
    sample_delay = 1.0 / settings.sample_fps
    frame_count = 0
    event_count = 0
    started_at = time.monotonic()
    last_sample_at = 0.0

    print("ATM Guard 已啟動。按 Ctrl+C 停止。")
    print(f"影像來源：{settings.camera_source}")
    print(f"OpenAI 模型：{settings.openai_model}")

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                print("讀取影像失敗，等待下一幀...")
                time.sleep(1)
                continue

            now = time.monotonic()
            if now - last_sample_at < sample_delay:
                continue
            last_sample_at = now
            frame_count += 1

            detection = detector.analyze(frame)
            elapsed = max(now - started_at, 1e-6)
            fps = frame_count / elapsed

            print(
                "\r"
                f"狀態 FPS={fps:.2f} | 人物={detection.person_count} | "
                f"停留={detection.linger_seconds:.1f}s | "
                f"遮擋={detection.is_occluded}",
                end="",
            )

            if not detection.event_type:
                continue

            screenshot_path = save_screenshot(frame, settings.log_dir)
            print(f"\n事件觸發：{detection.event_reason}")
            judge_result = judge.judge(
                screenshot_path,
                detection.event_reason or detection.event_type,
            )
            event_id = execute_actions(judge_result, db, detection, screenshot_path)
            event_count += 1
            print(
                f"事件已記錄 ID={event_id} | "
                f"風險等級={judge_result.risk_level} | 原因={judge_result.reason}"
            )
    except KeyboardInterrupt:
        elapsed = time.monotonic() - started_at
        print("\n\nATM Guard 已停止。")
        print(f"執行時間：{elapsed:.1f} 秒")
        print(f"處理幀數：{frame_count}")
        print(f"事件數量：{event_count}")
    finally:
        capture.release()


if __name__ == "__main__":
    run()
