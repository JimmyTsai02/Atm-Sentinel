from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import numpy as np
from ultralytics import YOLO


@dataclass
class DetectionResult:
    person_count: int
    max_confidence: float
    linger_seconds: float
    is_occluded: bool
    event_type: str | None
    event_reason: str | None


class ATMDetector:
    def __init__(
        self,
        model_path: str,
        confidence: float,
        linger_threshold_sec: int,
        event_cooldown_sec: int,
        occlusion_dark_ratio: float,
        occlusion_bright_ratio: float,
        occlusion_edge_density: float,
        occlusion_blur_variance: float,
        occlusion_stddev: float,
        occlusion_consecutive_frames: int,
    ) -> None:
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.linger_threshold_sec = linger_threshold_sec
        self.event_cooldown_sec = event_cooldown_sec
        self.occlusion_dark_ratio = occlusion_dark_ratio
        self.occlusion_bright_ratio = occlusion_bright_ratio
        self.occlusion_edge_density = occlusion_edge_density
        self.occlusion_blur_variance = occlusion_blur_variance
        self.occlusion_stddev = occlusion_stddev
        self.occlusion_consecutive_frames = max(1, occlusion_consecutive_frames)
        self._person_seen_since: float | None = None
        self._last_event_at = 0.0
        self._occlusion_hits = 0

    def analyze(self, frame: np.ndarray) -> DetectionResult:
        now = time.monotonic()
        person_count, max_confidence = self._detect_people(frame)
        is_occluded = self._is_camera_occluded(frame)

        if person_count > 0:
            if self._person_seen_since is None:
                self._person_seen_since = now
            linger_seconds = now - self._person_seen_since
        else:
            self._person_seen_since = None
            linger_seconds = 0.0

        event_type = None
        event_reason = None
        cooldown_elapsed = now - self._last_event_at >= self.event_cooldown_sec

        if is_occluded and cooldown_elapsed:
            event_type = "camera_occlusion"
            event_reason = "偵測到畫面大面積變暗，疑似遮擋攝影機"
            self._last_event_at = now
        elif (
            person_count > 0
            and linger_seconds >= self.linger_threshold_sec
            and cooldown_elapsed
        ):
            event_type = "lingering"
            event_reason = f"人物停留超過 {self.linger_threshold_sec} 秒，疑似徘徊"
            self._last_event_at = now

        return DetectionResult(
            person_count=person_count,
            max_confidence=max_confidence,
            linger_seconds=linger_seconds,
            is_occluded=is_occluded,
            event_type=event_type,
            event_reason=event_reason,
        )

    def _detect_people(self, frame: np.ndarray) -> tuple[int, float]:
        results = self.model.predict(frame, conf=self.confidence, verbose=False)
        person_count = 0
        max_confidence = 0.0

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = result.names.get(class_id, "")
                confidence = float(box.conf[0])
                if class_name == "person":
                    person_count += 1
                    max_confidence = max(max_confidence, confidence)

        return person_count, max_confidence

    def _is_camera_occluded(self, frame: np.ndarray) -> bool:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        dark_ratio = float(np.mean(gray < 30))
        bright_ratio = float(np.mean(gray > 225))
        brightness_stddev = float(np.std(gray))
        blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        edges = cv2.Canny(gray, 60, 140)
        edge_density = float(np.mean(edges > 0))

        is_dark_cover = dark_ratio >= self.occlusion_dark_ratio
        is_bright_cover = bright_ratio >= self.occlusion_bright_ratio
        is_low_texture_cover = (
            edge_density <= self.occlusion_edge_density
            and blur_variance <= self.occlusion_blur_variance
            and brightness_stddev <= self.occlusion_stddev
        )

        if is_dark_cover or is_bright_cover or is_low_texture_cover:
            self._occlusion_hits += 1
        else:
            self._occlusion_hits = 0

        return self._occlusion_hits >= self.occlusion_consecutive_frames
