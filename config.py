from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    openai_max_retries: int
    camera_index: int
    rtsp_url: str
    sample_fps: int
    frame_width: int
    frame_height: int
    yolo_model: str
    yolo_confidence: float
    linger_threshold_sec: int
    event_cooldown_sec: int
    occlusion_dark_ratio: float
    occlusion_bright_ratio: float
    occlusion_edge_density: float
    occlusion_blur_variance: float
    occlusion_stddev: float
    occlusion_consecutive_frames: int
    log_dir: Path
    db_path: Path

    @property
    def camera_source(self) -> int | str:
        return self.rtsp_url if self.rtsp_url else self.camera_index


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        openai_max_retries=_get_int("OPENAI_MAX_RETRIES", 3),
        camera_index=_get_int("CAMERA_INDEX", 0),
        rtsp_url=os.getenv("RTSP_URL", ""),
        sample_fps=max(1, _get_int("SAMPLE_FPS", 1)),
        frame_width=_get_int("FRAME_WIDTH", 640),
        frame_height=_get_int("FRAME_HEIGHT", 480),
        yolo_model=os.getenv("YOLO_MODEL", "yolov8n.pt"),
        yolo_confidence=_get_float("YOLO_CONFIDENCE", 0.5),
        linger_threshold_sec=_get_int("LINGER_THRESHOLD_SEC", 30),
        event_cooldown_sec=_get_int("EVENT_COOLDOWN_SEC", 20),
        occlusion_dark_ratio=_get_float("OCCLUSION_DARK_RATIO", 0.75),
        occlusion_bright_ratio=_get_float("OCCLUSION_BRIGHT_RATIO", 0.85),
        occlusion_edge_density=_get_float("OCCLUSION_EDGE_DENSITY", 0.015),
        occlusion_blur_variance=_get_float("OCCLUSION_BLUR_VARIANCE", 35.0),
        occlusion_stddev=_get_float("OCCLUSION_STDDEV", 28.0),
        occlusion_consecutive_frames=_get_int("OCCLUSION_CONSECUTIVE_FRAMES", 2),
        log_dir=Path(os.getenv("LOG_DIR", "logs")),
        db_path=Path(os.getenv("DB_PATH", "atm_guard.db")),
    )
