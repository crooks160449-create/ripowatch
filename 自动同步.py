# -*- coding: utf-8 -*-
"""
RepoWatch 自动同步工具

启动后，本程序会在后台监听 docs/ 和 mkdocs.yml：
  文件修改并停止 5 秒后，自动 git add + commit + push。

使用：
  python 自动同步.py

按 Ctrl+C 或直接关闭窗口即可退出。
"""

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


BASE_DIR = Path(__file__).resolve().parent
WATCH_PATHS = [BASE_DIR / "docs", BASE_DIR / "mkdocs.yml"]
DEBOUNCE_SECONDS = 5


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        src = event.src_path.replace("\\", "/")
        if "/.git/" in src or src.endswith("~") or src.endswith(".tmp"):
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SECONDS, self._fire)
            self._timer.start()

    def _fire(self):
        if self._callback:
            self._callback()


def run_git(args):
    result = subprocess.run(
        ["git"] + args,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result


def sync():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    result = run_git(["add", "."])
    if result.returncode != 0:
        print(f"[{now}] git add 失败：{result.stderr.strip()}")
        return

    changed = run_git(["diff", "--cached", "--quiet"])
    if changed.returncode == 0:
        print(f"[{now}] 没有新的修改")
        return

    message = f"自动同步 {now}"
    result = run_git(["commit", "-m", message])
    if result.returncode != 0:
        print(f"[{now}] git commit 失败：{result.stderr.strip()}")
        return

    for remote in ("origin", "tsinghua"):
        result = run_git(["push", remote, "main"])
        if result.returncode == 0:
            print(f"[{now}] 已推送到 {remote}")
        else:
            print(f"[{now}] 推送到 {remote} 失败：{result.stderr.strip()}")


def main():
    print("=" * 52)
    print("  RepoWatch 自动同步已启动")
    print(f"  监听目录：{BASE_DIR / 'docs'}")
    print(f"  防抖时间：{DEBOUNCE_SECONDS} 秒")
    print("  修改文件并保存后，将自动提交并推送")
    print("  按 Ctrl+C 退出")
    print("=" * 52)

    observer = Observer()
    handler = ChangeHandler(sync)
    for path in WATCH_PATHS:
        if path.is_dir():
            observer.schedule(handler, str(path), recursive=True)
        elif path.exists():
            observer.schedule(handler, str(path.parent), recursive=False)

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
