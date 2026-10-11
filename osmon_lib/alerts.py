"""告警规则：CPU / 内存 / 磁盘 / 温度 / 电源。"""

import os
from dataclasses import dataclass, asdict

import psutil

from . import hwinfo, power
from .ui import fmt_bytes, fmt_duration


@dataclass
class Thresholds:
    cpu: float = 80.0        # CPU 总使用率 %
    mem: float = 85.0        # 内存使用率 %
    swap: float = 50.0       # 交换分区使用率 %
    disk: float = 85.0       # 磁盘分区使用率 %
    temp: float = 85.0       # 温度 ℃
    battery: float = 20.0    # 电量 % 下限
    drain_watts: float = 25.0  # 放电功率 W 上限
    proc_cpu: float = 30.0   # 单进程 CPU % 上限
    proc_mem: float = 10.0   # 单进程 内存 % 上限

    @classmethod
    def from_env(cls) -> "Thresholds":
        mapping = {
            "cpu": "OSMON_CPU", "mem": "OSMON_MEM", "swap": "OSMON_SWAP",
            "disk": "OSMON_DISK", "temp": "OSMON_TEMP", "battery": "OSMON_BATTERY",
            "drain_watts": "OSMON_DRAIN", "proc_cpu": "OSMON_PROC_CPU",
            "proc_mem": "OSMON_PROC_MEM",
        }
        kwargs = {}
        for field, env in mapping.items():
            v = os.environ.get(env)
            if v:
                try:
                    kwargs[field] = float(v)
                except ValueError:
                    pass
        return cls(**kwargs)

    def update(self, **kwargs) -> "Thresholds":
        for k, v in kwargs.items():
            if v is not None and hasattr(self, k):
                setattr(self, k, float(v))
        return self


# psutil 的 cpu_percent(interval=None) 只有在同一个 Process 对象上二次调用才有意义，
# 因此缓存 Process 对象，保证刷新时能拿到真实占用率。
_PROC_CACHE: dict = {}


def prime_processes() -> None:
    """建立基线：首次调用返回值无意义，需在刷新前调用一次。"""
    refresh_processes()
    for p in _PROC_CACHE.values():
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    psutil.cpu_percent(interval=None)


def refresh_processes() -> dict:
    cur = {}
    for pid in psutil.pids():
        try:
            p = _PROC_CACHE.get(pid)
            if p is None:
                p = psutil.Process(pid)
            cur[pid] = p
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            continue
    _PROC_CACHE.clear()
    _PROC_CACHE.update(cur)
    return _PROC_CACHE


def top_processes(n: int = 5, by: str = "cpu") -> list:
    key = "cpu_percent" if by == "cpu" else "memory_percent"
    procs = []
    for p in refresh_processes().values():
        try:
            info = p.as_dict(attrs=["pid", "name", "cpu_percent", "memory_percent", "username"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if (info.get(key) or 0) <= 0:
            continue
        procs.append(info)
    procs.sort(key=lambda x: (x.get(key) or 0), reverse=True)
    return procs[:n]


def collect(th: Thresholds) -> list:
    """返回 [(级别, 来源, 说明)]，级别 ∈ {CRIT, WARN, INFO}。"""
    alerts = []

    cpu = psutil.cpu_percent(interval=0.3)
    if cpu >= th.cpu:
        alerts.append(("CRIT" if cpu >= 95 else "WARN", "CPU", f"总使用率 {cpu:.0f}% ≥ 阈值 {th.cpu:.0f}%"))

    vm = psutil.virtual_memory()
    if vm.percent >= th.mem:
        alerts.append(("CRIT" if vm.percent >= 95 else "WARN", "内存",
                       f"使用率 {vm.percent:.0f}% ≥ 阈值 {th.mem:.0f}%（可用 {fmt_bytes(vm.available)}）"))

    sw = psutil.swap_memory()
    if sw.total and sw.percent >= th.swap:
        alerts.append(("WARN", "交换分区", f"使用率 {sw.percent:.0f}% ≥ 阈值 {th.swap:.0f}%，可能发生换页卡顿"))

    from . import diskwatch
    for part in diskwatch.partitions():
        if part["percent"] >= th.disk:
            alerts.append(("CRIT" if part["percent"] >= 95 else "WARN", "磁盘",
                           f"{part['mount']} 已用 {part['percent']:.0f}% ≥ 阈值 {th.disk:.0f}%"
                           f"（剩余 {fmt_bytes(part['free'])}）"))

    temp = hwinfo.max_temp()
    if temp >= th.temp:
        alerts.append(("CRIT" if temp >= 95 else "WARN", "温度",
                       f"最高 {temp:.0f}℃ ≥ 阈值 {th.temp:.0f}℃，检查散热与负载"))

    bat = power.battery()
    if bat.get("present"):
        pct = bat.get("percent")
        if pct is not None and pct <= th.battery and bat.get("state") == "放电中":
            alerts.append(("CRIT" if pct <= 10 else "WARN", "电源",
                           f"电量 {pct:.0f}% ≤ 阈值 {th.battery:.0f}% 且正在放电"))
        rate = bat.get("rate_w") or 0
        if bat.get("state") == "放电中" and rate >= th.drain_watts:
            alerts.append(("WARN", "电源",
                           f"放电功率 {rate:.1f}W ≥ 阈值 {th.drain_watts:.0f}W，续航将明显缩短"))
        health = bat.get("health")
        if health is not None and health < 70:
            alerts.append(("WARN", "电池", f"健康度 {health:.1f}% < 70%，建议关注/更换"))
        left = bat.get("secsleft")
        if bat.get("state") == "放电中" and left and left > 0 and left < 1800:
            alerts.append(("CRIT", "电源", f"剩余续航仅 {fmt_duration(left)}"))

    for p in top_processes(3, "cpu"):
        if (p["cpu_percent"] or 0) >= th.proc_cpu:
            alerts.append(("WARN", "进程",
                           f"{p['name']}(pid {p['pid']}) 占用 CPU {p['cpu_percent']:.0f}%"))
    for p in top_processes(3, "mem"):
        if (p["memory_percent"] or 0) >= th.proc_mem:
            alerts.append(("WARN", "进程",
                           f"{p['name']}(pid {p['pid']}) 占用内存 {p['memory_percent']:.1f}%"))

    if not alerts:
        alerts.append(("INFO", "系统", "所有指标在阈值范围内"))
    return alerts


def render(alerts, th: Thresholds) -> str:
    from .ui import color, C, table

    icon = {"CRIT": color("● CRIT", C.RED, C.BOLD),
            "WARN": color("● WARN", C.YELLOW, C.BOLD),
            "INFO": color("● INFO", C.GREEN)}
    rows = [[icon.get(a[0], a[0]), a[1], a[2]] for a in alerts]
    head = table(["级别", "来源", "说明"], rows, aligns=["l", "l", "l"])
    ths = (f"阈值: CPU≥{th.cpu:.0f}% 内存≥{th.mem:.0f}% 磁盘≥{th.disk:.0f}% "
           f"温度≥{th.temp:.0f}℃ 电量≤{th.battery:.0f}% 放电≥{th.drain_watts:.0f}W "
           f"进程CPU≥{th.proc_cpu:.0f}% 进程内存≥{th.proc_mem:.0f}%")
    return head + "\n" + color(ths, C.DIM)


def as_dict(th: Thresholds) -> dict:
    return asdict(th)
