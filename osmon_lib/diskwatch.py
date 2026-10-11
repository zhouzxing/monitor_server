"""磁盘状态：分区用量 / IO 速率 / SMART 健康 / 大文件占用与“死代码”预警。"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

from .ui import fmt_bytes, progress

CACHE_DIR = Path(os.environ.get("OSMON_CACHE", Path.home() / ".cache" / "osmon"))

# 默认跳过的目录（构建缓存、依赖目录、版本库内部对象）
PRUNE_DEFAULT = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "target",
    ".m2", ".gradle", ".cache", ".npm", ".cargo", "dist-newstyle", ".tox",
}

_last_io = {"ts": None, "io": None}


# squashfs/snap 是只读镜像挂载，永远 100%，不参与容量告警
SKIP_FSTYPE = {"squashfs", "overlay", "iso9660", "udf", "ramfs"}
SKIP_MOUNT_PREFIX = ("/snap/", "/var/lib/snapd/")


def partitions() -> list:
    rows = []
    seen = set()
    for p in psutil.disk_partitions(all=False):
        if p.device in seen:
            continue
        seen.add(p.device)
        if p.fstype in SKIP_FSTYPE or p.mountpoint.startswith(SKIP_MOUNT_PREFIX):
            continue
        try:
            u = psutil.disk_usage(p.mountpoint)
        except (PermissionError, OSError):
            continue
        rows.append({
            "device": p.device,
            "mount": p.mountpoint,
            "fstype": p.fstype,
            "total": u.total,
            "used": u.used,
            "free": u.free,
            "percent": u.percent,
        })
    rows.sort(key=lambda r: -r["total"])
    return rows


def io_rates() -> dict:
    """返回自上次调用以来的读写速率（B/s）。首次调用返回 0。"""
    now = time.time()
    cur = psutil.disk_io_counters()
    rates = {"read": 0.0, "write": 0.0, "read_count": 0, "write_count": 0}
    if cur is None:
        return rates
    prev_ts, prev = _last_io["ts"], _last_io["io"]
    _last_io["ts"], _last_io["io"] = now, cur
    if prev is None or not prev_ts:
        return rates  # 首次采样无基线
    dt = max(1e-6, now - prev_ts)
    rates["read"] = (cur.read_bytes - prev.read_bytes) / dt
    rates["write"] = (cur.write_bytes - prev.write_bytes) / dt
    rates["read_count"] = cur.read_count - prev.read_count
    rates["write_count"] = cur.write_count - prev.write_count
    return rates


def devices() -> list:
    """列出块设备（lsblk 可用时用它，否则退化为分区设备）。"""
    try:
        out = subprocess.run(
            ["lsblk", "-d", "-n", "-o", "NAME,TYPE,SIZE,MODEL"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            devs = []
            for line in out.stdout.strip().splitlines():
                parts = line.split(None, 3)
                if len(parts) >= 3 and parts[1] == "disk":
                    devs.append({
                        "name": parts[0],
                        "path": f"/dev/{parts[0]}",
                        "size": parts[2],
                        "model": parts[3] if len(parts) > 3 else "",
                    })
            if devs:
                return devs
    except Exception:
        pass
    return [{"name": os.path.basename(r["device"]), "path": r["device"], "size": "—", "model": ""}
            for r in partitions()]


def smart_health(path: str) -> dict:
    """读取 SMART 健康状态；无权限/不支持时降级。"""
    res = {"device": path, "ok": None, "detail": "", "temp": None, "extra": ""}
    try:
        out = subprocess.run(["smartctl", "-H", "-A", path], capture_output=True, text=True, timeout=8)
    except FileNotFoundError:
        res["detail"] = "未安装 smartctl"
        return res
    except Exception as exc:
        res["detail"] = f"读取失败: {exc}"
        return res
    text = out.stdout + "\n" + (out.stderr or "")
    if "Permission denied" in text:
        res["detail"] = "需要 sudo 权限（sudo smartctl -H -A %s）" % path
        return res
    if "SMART overall-health" in text:
        res["ok"] = "PASSED" in text or "OK" in text
        for line in text.splitlines():
            if "SMART overall-health" in line:
                res["detail"] = line.split(":", 1)[-1].strip()
                break
    elif "Unknown USB bridge" in text or "Device does not support SMART" in text:
        res["detail"] = "设备不支持 SMART"
    else:
        res["detail"] = "无 SMART 信息"
    for line in text.splitlines():
        if "Temperature_Celsius" in line or "Temperature_Internal" in line:
            fields = line.split()
            if len(fields) >= 10:
                try:
                    res["temp"] = float(fields[9])
                except ValueError:
                    pass
            break
    return res


# ---------------- 大文件 / 死代码扫描 ----------------

def _cache_path(root: Path) -> Path:
    key = str(root.resolve()).replace("/", "_").strip("_")[:120]
    return CACHE_DIR / f"bigfiles_{key}.json"


def _dirmap_path(root: Path) -> Path:
    """目录指纹单独存放：体积可能达几十 MB，避免污染主结果缓存。"""
    return _cache_path(root).with_suffix(".dirmap.json")


def save_cache(root, payload: dict) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    rp = Path(str(root)).expanduser().resolve()
    p = _cache_path(rp)
    payload = dict(payload)
    dirmap = payload.pop("dirmap", None)
    p.write_text(json.dumps(payload, ensure_ascii=False))
    if dirmap is not None:
        _dirmap_path(rp).write_text(json.dumps(dirmap, ensure_ascii=False))
    return p


def load_cache(root, with_dirmap: bool = False) -> dict:
    rp = Path(str(root)).expanduser().resolve()
    p = _cache_path(rp)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if with_dirmap:
        mp = _dirmap_path(rp)
        try:
            data["dirmap"] = json.loads(mp.read_text()) if mp.exists() else {}
        except (OSError, json.JSONDecodeError):
            data["dirmap"] = {}
    return data


def scan_big_files(root: str, min_size: int, idle_days: float, top: int,
                   prune=PRUNE_DEFAULT, max_depth: int = 0, verbose: bool = True,
                   incremental: bool = True, ttl_days: float = 14.0) -> dict:
    """遍历 root，收集大于 min_size 的文件，并标记长期未访问（死代码）的文件。

    性能要点：
    1. 手写 scandir 迭代栈，避免 os.walk 的二次 stat 与 Path 对象开销；
       `is_dir(follow_symlinks=False)` 直接读 readdir 的 d_type，目录不 stat。
    2. **增量复用**：目录 mtime 未变且缓存未过期时，跳过该目录下所有文件的 stat，
       只对已知大文件重新取一次 stat（刷新体积/访问时间）；新增/删除文件都会改动
       目录 mtime，因此目录内的文件名集合是可信的。
    3. 缓存条目超过 ttl_days 时该目录强制全量重扫，避免「文件被改写但目录 mtime 不变」
       造成的长期偏差。
    """
    root_path = Path(root).expanduser().resolve()
    cutoff = time.time() - idle_days * 86400
    now = time.time()
    prune_set = set(prune)
    # 目录数太多时（本仓库约 50 万个），指纹 key 用 dev:inode 而不是路径字符串，
    # 可把索引从 ~100MB 压到 ~15MB；文件数低于该阈值的目录重扫成本极低，不值得索引。
    index_min_files = 50

    prev_dirs = {}
    if incremental:
        cached = load_cache(root, with_dirmap=True)
        if cached.get("min_size") == min_size:
            prev_dirs = cached.get("dirmap", {})

    found = []
    scanned = 0        # 实际 stat 过的文件数
    reused = 0         # 复用的目录数
    skipped_stats = 0  # 因复用而省下的 stat 次数
    dirmap = {}
    last_report = now

    def report():
        nonlocal last_report
        if verbose and time.time() - last_report > 1.0:
            last_report = time.time()
            progress(f"  复用目录 {reused:,} / 省下 stat {skipped_stats:,}；"
                     f"已 stat {scanned:,} 文件，命中 {len(found):,} 大文件…")

    def record(path, st):
        return {"path": path, "size": st.st_size,
                "atime": st.st_atime, "mtime": st.st_mtime,
                "cold": max(st.st_atime, st.st_mtime) < cutoff}

    # 目录迭代栈：(dirpath, depth)
    stack = [(str(root_path), 0)]
    while stack:
        dirpath, depth = stack.pop()
        try:
            with os.scandir(dirpath) as it:
                entries = list(it)
        except OSError:
            continue

        try:
            dstat = os.stat(dirpath)
            dir_key = f"{dstat.st_dev:x}:{dstat.st_ino:x}"
            dir_mtime = dstat.st_mtime
        except OSError:
            dir_key, dir_mtime = "", 0.0
        cache_entry = prev_dirs.get(dir_key) if prev_dirs else None
        fresh = bool(incremental and cache_entry
                     and cache_entry[0] == dir_mtime
                     and (now - cache_entry[1]) < ttl_days * 86400)
        kept: list = []          # 命中 min_size 的文件记录
        n_files = 0

        for e in entries:
            name = e.name
            try:
                if e.is_dir(follow_symlinks=False):
                    if name in prune_set:
                        continue
                    if not max_depth or depth + 1 < max_depth:
                        stack.append((e.path, depth + 1))
                    continue
            except OSError:
                continue
            n_files += 1
            path = e.path
            if fresh:
                # 复用模式：只对上次记录过的大文件重新 stat，其余全部跳过
                prev_size = cache_entry[2].get(name)
                if prev_size is None or prev_size < min_size:
                    skipped_stats += 1
                    continue
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                scanned += 1
                if st.st_size >= min_size:
                    kept.append(record(path, st))
                continue
            try:
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            scanned += 1
            if st.st_size >= min_size:
                kept.append(record(path, st))
            if verbose and scanned % 5000 == 0:
                report()

        found.extend(kept)
        if fresh:
            reused += 1
        if kept or n_files >= index_min_files:
            big_names = {os.path.basename(f["path"]): f["size"] for f in kept}
            dirmap[dir_key] = [dir_mtime, now, big_names]
        report()

    if verbose and sys.stderr.isatty():
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()

    found.sort(key=lambda f: -f["size"])
    cold = [f for f in found if f["cold"]]
    groups = {}
    for f in found:
        rel = os.path.relpath(f["path"], root_path)
        topdir = rel.split(os.sep)[0] if os.sep in rel else "(根目录文件)"
        g = groups.setdefault(topdir, {"size": 0, "count": 0, "cold_size": 0})
        g["size"] += f["size"]
        g["count"] += 1
        if f["cold"]:
            g["cold_size"] += f["size"]

    return {
        "root": str(root_path),
        "scanned_at": now,
        "min_size": min_size,
        "idle_days": idle_days,
        "scanned_files": scanned,
        "reused_dirs": reused,
        "skipped_stats": skipped_stats,
        "incremental": bool(prev_dirs),
        "big_files": found[:top],
        "big_count": len(found),
        "big_bytes": sum(f["size"] for f in found),
        "cold_count": len(cold),
        "cold_bytes": sum(f["size"] for f in cold),
        "cold_top": sorted(cold, key=lambda f: -f["size"])[:top],
        "groups": sorted(({"dir": k, **v} for k, v in groups.items()),
                         key=lambda g: -g["size"])[:top],
        "dirmap": dirmap,
    }


def is_core_dump(path: str) -> bool:
    """core / core.<pid> 属于进程崩溃转储，通常可直接删除。"""
    name = os.path.basename(path)
    return name == "core" or name.startswith("core.")


def _fmt_age(ts: float) -> str:
    days = (time.time() - ts) / 86400
    if days >= 365:
        return f"{days/365:.1f}年"
    if days >= 30:
        return f"{days/30:.1f}月"
    return f"{days:.0f}天"


def render_big_files(data: dict, top: int = 25, only_cold: bool = False) -> str:
    from .ui import color, C, table

    if not data:
        return color("没有缓存的扫描结果，先执行：osmon disk big --refresh", C.YELLOW)
    age_h = (time.time() - data.get("scanned_at", 0)) / 3600
    skipped = data.get("skipped_stats") or 0
    if skipped:
        scan_line = (f"本次 stat {data['scanned_files']:,} 次，增量跳过 {skipped:,} 次"
                     f"（复用 {data.get('reused_dirs', 0):,} 个未变目录）")
    else:
        scan_line = f"本次全量 stat {data['scanned_files']:,} 个文件"
    lines = [
        f"扫描根目录: {data['root']}   快照时间: {age_h:.1f} 小时前"
        + (color("（较旧，建议 --refresh）", C.YELLOW) if age_h > 24 else ""),
        scan_line,
        f"大文件(≥{fmt_bytes(data['min_size'])}): "
        f"{data['big_count']:,} 个 / {fmt_bytes(data['big_bytes'])}",
        f"其中 {data['idle_days']:.0f} 天未访问的“死代码”: "
        f"{color(str(data['cold_count']) + ' 个 / ' + fmt_bytes(data['cold_bytes']), C.YELLOW)}",
    ]
    rows = data.get("cold_top") if only_cold else data.get("big_files")
    rows = (rows or [])[:top]
    cores = [f for f in (rows or []) if is_core_dump(f["path"])]
    if cores:
        lines.append("其中 core dump 崩溃转储（通常可直接 rm）: "
                     + color(f"{len(cores)} 个 / {fmt_bytes(sum(f['size'] for f in cores))}", C.RED))
    lines.append("")
    if rows:
        lines.append(table(
            ["体积", "状态", "最后访问", "路径"],
            [[fmt_bytes(f["size"]),
              color("core", C.RED) if is_core_dump(f["path"])
              else (color("冷/死", C.YELLOW) if f["cold"] else color("在用", C.GREEN)),
              _fmt_age(f["atime"]), f["path"]] for f in rows],
            aligns=["r", "l", "r", "l"],
        ))
    groups = (data.get("groups") or [])[:10]
    if groups:
        lines += ["", "按一级目录汇总：", table(
            ["目录", "大文件数", "占用", "其中冷数据"],
            [[g["dir"], f"{g['count']:,}", fmt_bytes(g["size"]), fmt_bytes(g["cold_size"])]
             for g in groups],
            aligns=["l", "r", "r", "r"],
        )]
    return "\n".join(lines)
