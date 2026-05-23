from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import load_settings
from database import EventDatabase, EventRecord
from llm_judge import ATMVisionJudge
from tools import freeze_terminal, trigger_alert


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批次測試資料夾內的 ATM 圖片")
    parser.add_argument(
        "--folder",
        default="samples",
        help="測試圖片資料夾，預設為 samples",
    )
    parser.add_argument(
        "--hint",
        default="請檢查 ATM 圖片中是否有徘徊、偷看密碼、遮擋鏡頭、安裝異常裝置、戴安全帽或口罩操作 ATM 等風險",
        help="提供給 GPT-4o 的事件提示",
    )
    return parser.parse_args()


def find_images(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def main() -> None:
    args = parse_args()
    folder = Path(args.folder)
    if not folder.exists():
        raise FileNotFoundError(f"找不到資料夾：{folder}")

    images = find_images(folder)
    if not images:
        print(f"資料夾內沒有可測試圖片：{folder}")
        return

    settings = load_settings()
    judge = ATMVisionJudge(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        max_retries=settings.openai_max_retries,
    )
    db = EventDatabase(settings.db_path)

    print(f"開始批次測試，共 {len(images)} 張圖片。")

    for index, image_path in enumerate(images, start=1):
        print(f"\n[{index}/{len(images)}] 測試圖片：{image_path}")
        result = judge.judge(image_path, args.hint)

        if "trigger_alert" in result.actions:
            trigger_alert(result.risk_level, result.reason)
        if "freeze_terminal" in result.actions:
            freeze_terminal(result.risk_level, result.reason)

        event_id = db.log_event(
            EventRecord(
                risk_level=result.risk_level,
                reason=result.reason,
                event_type="folder_image_test",
                screenshot_path=str(image_path),
                actions=json.dumps(result.actions, ensure_ascii=False),
            )
        )

        print(f"事件 ID：{event_id}")
        print(f"風險等級：{result.risk_level}")
        print(f"原因：{result.reason}")
        print(f"執行動作：{', '.join(result.actions)}")

    print("\n批次圖片測試完成。")


if __name__ == "__main__":
    main()
