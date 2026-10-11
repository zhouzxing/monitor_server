"""终端渲染辅助：颜色、进度条、表格、单位格式化。"""

import os
import shutil
import sys
import time

ENABLE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def set_color(enabled: bool) -> None:
    global ENABLE_COLOR
    ENABLE_COLOR = enabled


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BG_RED = "\033[41m"


def display_width(s: str) -> int:
    """终端显示宽度：去掉 ANSI 转义，中文/全角按 2 计。"""
    import re
    import unicodedata

    plain = re.sub(r"\033\[[0-9;]*m", "", str(s))
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in plain)


def color(text: str, *codes: str) -> str:
    if not ENABLE_COLOR or not codes:
        return text
    return "".join(codes) + text + C.RESET


def level_color(pct: float, warn: float, crit: float) -> str:
    if pct >= crit:
        return C.RED
    if pct >= warn:
        return C.YELLOW
    return C.GREEN


def bar(pct: float, width: int = 24, warn: float = 70, crit: float = 90) -> str:
    """返回带颜色的文本进度条。pct 为 0~100。"""
    pct = max(0.0, min(100.0, pct))
    filled = int(round(pct / 100 * width))
    body = "█" * filled + "·" * (width - filled)
    return color(body, level_color(pct, warn, crit))


def fmt_bytes(n: float, suffix: str = "B") -> str:
    n = float(n)
    for unit in ("", "K", "M", "G", "T", "P"):
        if abs(n) < 1024.0:
            return f"{n:3.1f}{unit}{suffix}" if unit else f"{n:.0f}{suffix}"
        n /= 1024.0
    return f"{n:.1f}E{suffix}"


def fmt_rate(bytes_per_sec: float) -> str:
    return f"{fmt_bytes(bytes_per_sec)}/s" if bytes_per_sec else "0B/s"


def fmt_freq(mhz: float) -> str:
    return f"{mhz/1000:.2f} GHz" if mhz >= 1000 else f"{mhz:.0f} MHz"


def fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 0:
        return "未知"
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}天{h}小时{m}分"
    if h:
        return f"{h}小时{m}分"
    return f"{m}分{s}秒"


def fmt_watts(w: float) -> str:
    return f"{w:.1f} W"


def table(headers, rows, aligns=None) -> str:
    """渲染对齐的纯文本表格（支持 ANSI 颜色，按可见宽度对齐，中文按 2 列宽）。"""
    def visible(s: str) -> int:
        return display_width(s)

    rows = [[str(c) for c in r] for r in rows]
    all_rows = [list(headers)] + rows
    widths = [max(visible(r[i]) for r in all_rows) for i in range(len(headers))]
    aligns = aligns or ["l"] * len(headers)

    def line(cells, sep=" | "):
        out = []
        for i, cell in enumerate(cells):
            pad = widths[i] - visible(cell)
            if aligns[i] == "r":
                out.append(" " * pad + cell)
            else:
                out.append(cell + " " * pad)
        return sep.join(out).rstrip()

    lines = [color(line(headers), C.BOLD)]
    lines.append("─" * (sum(widths) + 3 * (len(headers) - 1)))
    for r in rows:
        lines.append(line(r))
    return "\n".join(lines)


def kv(pairs, indent: str = "  ") -> str:
    width = max(display_width(k) for k, _ in pairs)
    return "\n".join(
        f"{indent}{k}{' ' * (width - display_width(k))} : {v}" for k, v in pairs
    )


def panel(title: str, body: str, width: int = 78) -> str:
    tw = display_width(title)
    head = f"┌─ {title} " + "─" * max(0, width - tw - 4) + "┐"
    tail = "└" + "─" * (width - 2) + "┘"
    return "\n".join([head, body, tail])


def clear_screen() -> None:
    if sys.stdout.isatty():
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def term_width(default: int = 100) -> int:
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default


def progress(msg: str) -> None:
    """向 stderr 输出单行进度（非 tty 时不刷屏）。"""
    if sys.stderr.isatty():
        sys.stderr.write("\r\033[K" + msg)
        sys.stderr.flush()
    elif int(time.time()) % 10 == 0:
        sys.stderr.write(msg + "\n")
