"""电源与耗电：电池 / AC / 整机功耗估算 / RAPL。"""

import os
import subprocess
import time

import psutil

from .ui import fmt_watts

POWER_SUPPLY = "/sys/class/power_supply"
RAPL = "/sys/class/powercap"


def _read(path: str):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def _upower_battery() -> dict:
    """upower 提供 energy-rate(实时功率)、健康度、循环次数，无需 root。"""
    info = {}
    try:
        out = subprocess.run(
            ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT1"],
            capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return info
    if out.returncode != 0:
        return info
    for line in out.stdout.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if k == "state":
            info["state"] = v
        elif k == "energy":
            info["energy_wh"] = _num(v)
        elif k == "energy-full":
            info["energy_full_wh"] = _num(v)
        elif k == "energy-full-design":
            info["energy_design_wh"] = _num(v)
        elif k == "energy-rate":
            info["rate_w"] = _num(v)
        elif k == "voltage":
            info["voltage"] = _num(v)
        elif k == "percentage":
            info["percent"] = _num(v)
        elif k == "capacity":
            info["health"] = _num(v)
        elif k == "charge-cycles":
            info["cycles"] = _num(v)
        elif k == "time to empty":
            info["time_to_empty"] = v
        elif k == "time to full":
            info["time_to_full"] = v
        elif k == "model":
            info["model"] = v
    return info


def _num(v: str):
    try:
        return float(v.split()[0].replace(",", "."))
    except (ValueError, IndexError):
        return None


def battery() -> dict:
    res = {
        "present": False, "percent": None, "plugged": None, "secsleft": None,
        "state": "—", "rate_w": None, "energy_wh": None, "energy_full_wh": None,
        "energy_design_wh": None, "health": None, "cycles": None, "voltage": None,
        "model": None, "time_to_empty": None, "time_to_full": None,
    }
    bat = psutil.sensors_battery()
    if bat:
        res.update({
            "present": True,
            "percent": bat.percent,
            "plugged": bat.power_plugged,
            "secsleft": None if bat.secsleft in (-1, -2) else bat.secsleft,
        })
    up = _upower_battery()
    for k, v in up.items():
        if v is not None:
            res[k] = v
    if res["present"] and not res.get("model"):
        res["model"] = _read(f"{POWER_SUPPLY}/BAT1/model_name")
    if res.get("state") == "—":
        st = _read(f"{POWER_SUPPLY}/BAT1/status")
        if st:
            res["state"] = {"Charging": "充电中", "Discharging": "放电中",
                            "Full": "已充满", "Not charging": "未充电"}.get(st, st)
    else:
        res["state"] = {"charging": "充电中", "discharging": "放电中",
                        "fully-charged": "已充满", "pending-charge": "等待充电",
                        "empty": "电量耗尽"}.get(res.get("state"), res.get("state"))
    if res.get("plugged") is None:
        online = _read(f"{POWER_SUPPLY}/ACAD/online") or _read(f"{POWER_SUPPLY}/AC/online")
        res["plugged"] = online == "1"
    if res.get("health") is None and res.get("energy_full_wh") and res.get("energy_design_wh"):
        res["health"] = res["energy_full_wh"] / res["energy_design_wh"] * 100
    return res


def rapl_power() -> dict:
    """从 Intel RAPL 读取 CPU/内存功耗（多数发行版需要 root）。"""
    out = {"available": False, "domains": [], "watts": None}
    if not os.path.isdir(RAPL):
        return out
    try:
        entries = sorted(e for e in os.listdir(RAPL) if e.startswith("intel-rapl"))
    except OSError:
        return out
    for e in entries:
        name = _read(f"{RAPL}/{e}/name")
        energy = _read(f"{RAPL}/{e}/energy_uj")
        max_range = _read(f"{RAPL}/{e}/max_energy_range_uj")
        watts = None
        if energy and max_range:
            try:
                # 单次采样无法算功率，这里只回报可读性与能量计数存在性
                watts = None
                out["available"] = True
            except ValueError:
                pass
        out["domains"].append({"name": name or e, "path": f"{RAPL}/{e}", "readable": energy is not None})
    return out


def rapl_sample(interval: float = 0.5) -> dict:
    """两次采样 energy_uj 计算实际功率（需要读权限）。"""
    result = {"ok": False, "domains": []}

    def read_all():
        data = {}
        try:
            for e in sorted(x for x in os.listdir(RAPL) if x.startswith("intel-rapl")):
                name = _read(f"{RAPL}/{e}/name") or e
                energy = _read(f"{RAPL}/{e}/energy_uj")
                if energy:
                    try:
                        data[name] = (float(energy), time.time())
                    except ValueError:
                        pass
        except OSError:
            pass
        return data

    first = read_all()
    if not first:
        return result
    time.sleep(interval)
    second = read_all()
    for name, (e0, t0) in first.items():
        if name in second:
            e1, t1 = second[name]
            dt = max(1e-6, t1 - t0)
            de = e1 - e0
            if de < 0:  # 计数器回绕
                continue
            result["domains"].append({"name": name, "watts": de / 1e6 / dt})
    result["ok"] = bool(result["domains"])
    return result


def estimate_cpu_watts(tdp: float = 15.0, util: float = None) -> float:
    """无 RAPL 权限时的粗略估算：待机 8% TDP + 利用率 × 92% TDP。"""
    if util is None:
        util = psutil.cpu_percent(interval=0.0)
    return tdp * (0.08 + 0.92 * max(0.0, min(100.0, util)) / 100)


def total_draw_watts(bat: dict, cpu_watts: float) -> float:
    """整机耗电：优先用电池放电功率（真实测量），否则用 CPU 估算 + 基础平台功耗。"""
    if bat.get("rate_w") and bat.get("state") == "放电中":
        return bat["rate_w"]
    return cpu_watts + 6.0  # 平台基础功耗（屏幕/硬盘/无线）粗估 6W


def snapshot(tdp: float = 15.0) -> dict:
    bat = battery()
    rapl = rapl_sample()
    cpu_w = rapl["domains"][0]["watts"] if rapl.get("ok") and rapl["domains"] else None
    if cpu_w is None:
        cpu_w = estimate_cpu_watts(tdp)
        cpu_source = f"估算(TDP {tdp:.0f}W)"
    else:
        cpu_source = "RAPL实测"
    return {
        "battery": bat,
        "cpu_watts": cpu_w,
        "cpu_source": cpu_source,
        "rapl_readable": rapl.get("ok", False),
        "total_watts": total_draw_watts(bat, cpu_w),
    }


def render(info: dict) -> str:
    from .ui import color, C, fmt_duration, kv

    bat = info["battery"]
    lines = []
    if not bat["present"]:
        lines.append(color("未检测到电池（台式机或虚拟机），仅显示功耗估算。", C.DIM))
    else:
        pct = bat.get("percent")
        pct_s = f"{pct:.0f}%" if pct is not None else "—"
        level = C.GREEN if (pct or 100) > 40 else (C.YELLOW if (pct or 0) > 20 else C.RED)
        left = bat.get("time_to_empty")
        if not left and bat.get("secsleft"):
            left = fmt_duration(bat["secsleft"])
        rows = [
            ("电池型号", bat.get("model") or "—"),
            ("电量", color(pct_s, level, C.BOLD)),
            ("状态", bat.get("state", "—")),
            ("AC 接入", "是" if bat.get("plugged") else color("否（使用电池）", C.YELLOW)),
            ("实时功率", fmt_watts(bat["rate_w"]) if bat.get("rate_w") is not None else "—"),
            ("剩余容量", f"{bat['energy_wh']:.1f} Wh / {bat['energy_full_wh']:.1f} Wh"
             if bat.get("energy_wh") and bat.get("energy_full_wh") else "—"),
            ("设计容量", f"{bat['energy_design_wh']:.1f} Wh" if bat.get("energy_design_wh") else "—"),
            ("健康度", (f"{bat['health']:.1f}%" if bat.get("health") else "—")),
            ("循环次数", str(int(bat["cycles"])) if bat.get("cycles") else "—"),
            ("电压", f"{bat['voltage']:.2f} V" if bat.get("voltage") else "—"),
            ("可用时间", left or "—"),
        ]
        lines.append(kv(rows))
    lines.append("")
    lines.append(kv([
        ("CPU 功耗", f"{fmt_watts(info['cpu_watts'])}（{info['cpu_source']}）"),
        ("整机估算", color(fmt_watts(info["total_watts"]), C.BOLD)
         + ("（电池实测）" if bat.get("rate_w") and bat.get("state") == "放电中" else "（CPU+平台6W估算）")),
        ("RAPL", "可读" if info["rapl_readable"] else "不可读（需 root，退化为估算）"),
    ]))
    return "\n".join(lines)
