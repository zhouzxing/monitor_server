"""硬件状态采集（CPU-Z 风格）：CPU / 内存 / 主板 / 显卡 / 系统 / 温度。"""

import os
import platform
import re
import subprocess
import time

import psutil

from .ui import fmt_bytes, fmt_freq

DMI = "/sys/devices/virtual/dmi/id"


def _run(cmd, timeout=3):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _dmi(name):
    try:
        with open(os.path.join(DMI, name)) as f:
            return f.read().strip()
    except OSError:
        return ""


def _read(path: str):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def _lscpu_map():
    data = {}
    for line in _run(["lscpu"]).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def cpu_info() -> dict:
    info = _lscpu_map()
    freq = psutil.cpu_freq()
    try:
        cur = psutil.cpu_percent(interval=0.0)
    except Exception:
        cur = 0.0
    caches = []
    for key in ("L1d cache", "L1i cache", "L2 cache", "L3 cache"):
        if info.get(key):
            caches.append(f"{key.split()[0]}={info[key].split('(')[0].strip()}")
    flags = info.get("Flags", "").split()
    interesting = [f for f in ("avx2", "avx512f", "sse4_2", "vmx", "svm", "aes", "ht") if f in flags]
    model = info.get("Model name") or platform.processor() or "未知"

    def base_freq() -> str:
        if info.get("CPU MHz"):
            try:
                return fmt_freq(float(info["CPU MHz"]))
            except ValueError:
                pass
        # sysfs base_frequency 单位是 kHz
        raw = _read("/sys/devices/system/cpu/cpu0/cpufreq/base_frequency")
        if raw:
            try:
                return fmt_freq(float(raw) / 1000)
            except ValueError:
                pass
        m = re.search(r"@\s*([\d.]+)\s*GHz", model)
        return f"{float(m.group(1)):.2f} GHz" if m else "—"

    return {
        "型号": model,
        "厂商": info.get("Vendor ID", "—"),
        "架构": info.get("Architecture", platform.machine()),
        "物理核心": psutil.cpu_count(logical=False) or info.get("Core(s) per socket", "—"),
        "逻辑处理器": psutil.cpu_count(logical=True),
        "插槽数": info.get("Socket(s)", "—"),
        "每核线程": info.get("Thread(s) per core", "—"),
        "基础频率": base_freq(),
        "当前频率": fmt_freq(freq.current) if freq else "—",
        "最大频率": fmt_freq(freq.max) if freq and freq.max else (info.get("CPU max MHz", "—") + " MHz" if info.get("CPU max MHz") else "—"),
        "缓存": " ".join(caches) or "—",
        "虚拟化": info.get("Virtualization", "—"),
        "指令集": ",".join(interesting) or "—",
        "当前负载": f"{cur:.0f}%",
        "BogoMIPS": info.get("BogoMIPS", "—"),
    }


def memory_info() -> dict:
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    return {
        "内存总量": fmt_bytes(vm.total),
        "已用": f"{fmt_bytes(vm.used)} ({vm.percent:.0f}%)",
        "可用": fmt_bytes(vm.available),
        "缓存/缓冲": fmt_bytes(getattr(vm, "cached", 0) + getattr(vm, "buffers", 0)),
        "交换分区": f"{fmt_bytes(sw.total)} (已用 {sw.percent:.0f}%)" if sw.total else "未启用",
        "内存类型": _mem_type(),
    }


def _mem_type() -> str:
    """尽力获取内存条信息，需要 root 权限的 dmidecode 失败时降级。"""
    out = _run(["sudo", "-n", "dmidecode", "-t", "memory"], timeout=4)
    if "DDR" in out:
        sizes = re.findall(r"Size:\s*(\d+\s*\w+)", out)
        types = re.findall(r"Type:\s*(\w+)", out)
        speeds = re.findall(r"Speed:\s*(\d+\s*\w+/?s?)", out)
        usable = [s for s in sizes if not s.startswith("No")]
        if usable:
            detail = " / ".join(usable)
            if types:
                detail += f" {types[0]}"
            if speeds:
                detail += f" {speeds[0]}"
            return detail
    return "—（需 sudo dmidecode 才能读取内存型号/频率）"


def board_info() -> dict:
    parts = [p for p in (_dmi("bios_vendor"), _dmi("bios_version")) if p]
    if _dmi("bios_date"):
        parts.append(f"({_dmi('bios_date')})")
    return {
        "产品": " ".join(p for p in (_dmi("product_vendor"), _dmi("product_name")) if p) or "—",
        "主板": " ".join(p for p in (_dmi("board_vendor"), _dmi("board_name")) if p) or "—",
        "BIOS": " ".join(parts) or "—",
        "序列号": _dmi("product_serial") or "—",
    }


def gpu_info() -> list:
    out = _run(["lspci"])
    gpus = [
        line.split(": ", 1)[1]
        for line in out.splitlines()
        if re.search(r"VGA|3D controller|Display controller", line)
    ]
    return gpus or ["—"]


def os_info() -> dict:
    up = time.time() - psutil.boot_time()
    days, rem = divmod(int(up), 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    distro = "未知"
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    distro = line.split("=", 1)[1].strip().strip('"')
                    break
    except OSError:
        distro = f"{platform.system()} {platform.release()}"
    return {
        "主机名": platform.node(),
        "系统": distro,
        "内核": platform.release(),
        "运行时间": f"{days}天{hours}小时{mins}分",
        "平均负载": f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}",
        "进程数": len(psutil.pids()),
    }


def temps() -> dict:
    """返回 {chip: [(label, current, high, critical)]}"""
    result = {}
    try:
        raw = psutil.sensors_temperatures()
    except Exception:
        raw = {}
    for chip, entries in raw.items():
        items = []
        for e in entries:
            items.append((e.label or chip, e.current, e.high, e.critical))
        if items:
            result[chip] = items
    return result


def fans() -> dict:
    try:
        return {chip: [(e.label or chip, e.current) for e in entries]
                for chip, entries in psutil.sensors_fans().items() if entries}
    except Exception:
        return {}


def max_temp(default=0.0) -> float:
    """整机最高温度（用于预警）。"""
    vals = [c for items in temps().values() for (_, c, _, _) in items]
    return max(vals) if vals else default


def snapshot() -> dict:
    return {
        "os": os_info(),
        "cpu": cpu_info(),
        "memory": memory_info(),
        "board": board_info(),
        "gpu": gpu_info(),
        "temps": temps(),
        "fans": fans(),
    }
