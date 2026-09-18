# -*- coding: utf-8 -*-
"""
课程内容自动同步工具（给老师和助教使用）

监听课程内容文件夹，自动处理两类文件：
  1. 文档/课件（docs、md 等）→ 自动 git add + commit + push
  2. 视频（media/videos/*.mp4 等）→ 生成视频索引 videos.json，不提交 Git

老师只需要做一件事：把文件放进文件夹、保存。
"""

import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("缺少 watchdog 库，请先执行：")
    print("  pip install watchdog")
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

WATCH_DIR = Path(__file__).resolve().parent
MEDIA_DIR = WATCH_DIR / "media"
VIDEOS_DIR = MEDIA_DIR / "videos"
VIDEO_INDEX = MEDIA_DIR / "videos.json"
DEBOUNCE_SECONDS = 2
REMOTE = "origin"
BRANCH = "main"

VIDEO_EXTS = {".mp4", ".webm", ".m4v", ".mov", ".mkv"}


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_git(args):
    return subprocess.run(
        ["git"] + args,
        cwd=str(WATCH_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def regenerate_video_index():
    """扫描 media/videos/，生成 videos.json 索引。"""
    try:
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        videos = sorted(
            p.name for p in VIDEOS_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in VIDEO_EXTS
        )
        VIDEO_INDEX.write_text(
            json.dumps(videos, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[{now_str()}] 视频索引已更新：{len(videos)} 个视频")
        return videos
    except Exception as exc:
        print(f"[{now_str()}] 更新视频索引失败：{exc}")
        return []


def sync_git():
    """自动提交并推送文档改动（排除 media 目录）。"""
    ts = now_str()

    result = run_git(["add", "-A", "--", ".", ":!media"])
    if result.returncode != 0:
        print(f"[{ts}] git add 失败：{result.stderr.strip()}")
        return

    check = run_git(["diff", "--cached", "--quiet"])
    if check.returncode == 0:
        print(f"[{ts}] 没有新的文档修改，跳过提交")
        return

    message = f"自动同步 {ts}"
    result = run_git(["commit", "-m", message])
    if result.returncode != 0:
        print(f"[{ts}] git commit 失败：{result.stderr.strip()}")
        return
    print(f"[{ts}] 已提交：{message}")

    result = run_git(["push", REMOTE, BRANCH])
    if result.returncode == 0:
        print(f"[{ts}] 已推送到清华 Git，网站将在 1-3 分钟内自动更新")
    else:
        print(f"[{ts}] 推送失败：{result.stderr.strip()}")


# ---------------------------------------------------------------------------
# 文件监听
# ---------------------------------------------------------------------------

class ChangeHandler(FileSystemEventHandler):
    """把 media 目录和普通文件的变化分开处理。"""

    def __init__(self, git_callback, video_callback):
        super().__init__()
        self._git_callback = git_callback
        self._video_callback = video_callback
        self._git_timer = None
        self._video_timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        src = event.src_path.replace("\\", "/")
        if "/.git/" in src or src.endswith(".git"):
            return
        if src.endswith("~") or src.endswith(".tmp"):
            return

        with self._lock:
            if "/media/" in src:
                if self._video_timer:
                    self._video_timer.cancel()
                self._video_timer = threading.Timer(
                    DEBOUNCE_SECONDS, self._fire_video)
                self._video_timer.start()
            else:
                if self._git_timer:
                    self._git_timer.cancel()
                self._git_timer = threading.Timer(
                    DEBOUNCE_SECONDS, self._fire_git)
                self._git_timer.start()

    def _fire_git(self):
        if self._git_callback:
            self._git_callback()

    def _fire_video(self):
        if self._video_callback:
            self._video_callback()


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    print("=" * 58)
    print("  课程内容自动同步工具")
    print(f"  监听文件夹：{WATCH_DIR}")
    print(f"  视频目录：{VIDEOS_DIR}")
    print(f"  防抖时间：{DEBOUNCE_SECONDS} 秒")
    print("  文档改动 → 自动提交推送；视频改动 → 自动更新索引")
    print("  退出：关闭本窗口，或按 Ctrl+C")
    print("=" * 58)
    print()

    # 启动时先生成一次索引，确保目录和索引存在
    regenerate_video_index()

    observer = Observer()
    handler = ChangeHandler(sync_git, regenerate_video_index)
    observer.schedule(handler, str(WATCH_DIR), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
