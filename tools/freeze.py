from __future__ import annotations

from colorama import Back, Fore, Style, init

init(autoreset=True)


def freeze_terminal(risk_level: int, reason: str) -> None:
    print(Back.BLACK + Fore.WHITE + Style.BRIGHT)
    print("=" * 72)
    print("ATM 已進入模擬凍結狀態")
    print(f"風險等級：{risk_level}")
    print(f"原因：{reason}")
    print("=" * 72)
    print(Style.RESET_ALL)
