from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI


SYSTEM_PROMPT = """You are a security monitoring AI for an ATM machine.
Analyze the provided image and assess the risk level of the behavior shown.

Risk levels:
1 = Normal ATM usage, no suspicious behavior
2 = Suspicious: lingering > 30s, repeatedly approaching terminal, unnatural posture,
    using ATM while wearing a face mask, or using ATM while wearing a helmet
3 = High risk: covering camera, attaching device to ATM, violent behavior

Policy:
- If a person is actively using the ATM while wearing a helmet or face mask,
  classify it as at least risk level 2 because it violates ATM security policy.
- If the helmet or face mask is combined with covering the camera, attaching a
  device, or violent behavior, classify it as risk level 3.

Always respond using the provided function tools.
Be concise in your reason field (max 100 chars)."""


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "log_event",
            "description": "記錄 ATM 監控事件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "integer", "enum": [1, 2, 3]},
                    "reason": {"type": "string", "maxLength": 100},
                },
                "required": ["risk_level", "reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_alert",
            "description": "當風險等級 >= 2 時觸發本地警報。",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "integer", "enum": [2, 3]},
                    "reason": {"type": "string", "maxLength": 100},
                },
                "required": ["risk_level", "reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "freeze_terminal",
            "description": "當風險等級 = 3 時以 terminal 模擬凍結。",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "integer", "enum": [3]},
                    "reason": {"type": "string", "maxLength": 100},
                },
                "required": ["risk_level", "reason"],
                "additionalProperties": False,
            },
        },
    },
]


@dataclass
class JudgeResult:
    risk_level: int
    reason: str
    actions: list[str]


class ATMVisionJudge:
    def __init__(self, api_key: str, model: str, max_retries: int) -> None:
        if not api_key:
            raise ValueError("找不到 OPENAI_API_KEY，請先在 .env 設定你的 API key。")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries

    def judge(self, image_path: Path, event_hint: str) -> JudgeResult:
        image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "ATM 監控事件提示："
                                        f"{event_hint}。請判斷風險等級並呼叫適當工具。"
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}"
                                    },
                                },
                            ],
                        },
                    ],
                    tools=TOOLS,
                    tool_choice="auto",
                )
                message = response.choices[0].message
                return self._parse_tool_calls(message.tool_calls, message.content)
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(min(2**attempt, 8))

        raise RuntimeError(f"OpenAI Vision 判斷失敗：{last_error}") from last_error

    def _parse_tool_calls(self, tool_calls: Any, content: str | None) -> JudgeResult:
        actions: list[str] = []
        risk_level = 1
        reason = "未偵測到明確異常"

        if tool_calls:
            for call in tool_calls:
                name = call.function.name
                args = json.loads(call.function.arguments or "{}")
                if name not in actions:
                    actions.append(name)
                risk_level = max(risk_level, int(args.get("risk_level", risk_level)))
                reason = str(args.get("reason", reason))[:100]
        elif content:
            reason = content[:100]

        if "log_event" not in actions:
            actions.append("log_event")
        if risk_level >= 2 and "trigger_alert" not in actions:
            actions.append("trigger_alert")
        if risk_level == 3 and "freeze_terminal" not in actions:
            actions.append("freeze_terminal")

        return JudgeResult(risk_level=risk_level, reason=reason, actions=actions)
