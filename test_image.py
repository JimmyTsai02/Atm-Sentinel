from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import load_settings
from database import EventDatabase, EventRecord
from llm_judge import ATMVisionJudge
from tools import freeze_terminal, trigger_alert


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="用單張圖片測試 ATM Guard GPT-4o 判斷流程")
    parser.add_argument("image", help="要測試的圖片路徑，例如 samples\\suspicious.jpg")
    parser.add_argument(
        "--hint",
        default="單張 ATM 監控測試圖片",
        help="提供給 GPT-4o 的事件提示",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(f"找不到圖片：{image_path}")

    settings = load_settings()
    judge = ATMVisionJudge(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        max_retries=settings.openai_max_retries,
    )
    db = EventDatabase(settings.db_path)

    result = judge.judge(image_path, args.hint)

    if "trigger_alert" in result.actions:
        trigger_alert(result.risk_level, result.reason)
    if "freeze_terminal" in result.actions:
        freeze_terminal(result.risk_level, result.reason)

    event_id = db.log_event(
        EventRecord(
            risk_level=result.risk_level,
            reason=result.reason,
            event_type="manual_image_test",
            screenshot_path=str(image_path),
            actions=json.dumps(result.actions, ensure_ascii=False),
        )
    )

    print("\n圖片測試完成")
    print(f"事件 ID：{event_id}")
    print(f"風險等級：{result.risk_level}")
    print(f"原因：{result.reason}")
    print(f"執行動作：{', '.join(result.actions)}")


if __name__ == "__main__":
    main()
