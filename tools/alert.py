from __future__ import annotations

from colorama import Fore, Style, init

init(autoreset=True)


def trigger_alert(risk_level: int, reason: str) -> None:
    print(
        Fore.RED
        + Style.BRIGHT
        + f"\n[警報] 風險等級 {risk_level}：{reason}\a"
        + Style.RESET_ALL
    )
