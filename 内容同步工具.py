# -*- coding: utf-8 -*-
"""
课程内容自动同步工具（给老师和助教使用）

用途：
  监听当前文件夹（课程内容仓库），老师编辑并保存文件后，
  自动执行 git add + commit + push，无需老师输入任何 git 命令。

使用方法：
  双击「启动内容同步.bat」，或者运行：
      python 内容同步工具.py

原理：
  文件变化 → 停止 2 秒（防抖）→ 自动提交并推送到清华 Git。
  老师只需要做一件事：改文件、保存。
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
    print("如果连 pip 都不会用，请找开发者帮忙安装。")
    input("\n按回车键退出...")
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

WATCH_DIR = Path(__file__).resolve().parent   # 监听脚本所在文件夹
DEBOUNCE_SECONDS = 2                          # 停止修改 2 秒后才提交
REMOTE = "origin"                             # 推送到的远程仓库名
BRANCH = "main"                               # 推送分支


# ---------------------------------------------------------------------------
# Git 操作
# ---------------------------------------------------------------------------

def run_git(args):
    """执行 git 命令，返回 CompletedProcess。"""
    return subprocess.run(
        ["git"] + args,
        cwd=str(WATCH_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sync():
    """自动提交并推送所有变化。"""
    ts = now_str()

    result = run_git(["add", "-A"])
    if result.returncode != 0:
        print(f"[{ts}] git add 失败：{result.stderr.strip()}")
        return

    # 检查是否有需要提交的变化
    check = run_git(["diff", "--cached", "--quiet"])
    if check.returncode == 0:
        print(f"[{ts}] 没有新的修改，跳过提交")
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
        print("    提示：请检查网络，或确认 git 已登录清华 Git")


# ---------------------------------------------------------------------------
# 文件监听
# ---------------------------------------------------------------------------

class ChangeHandler(FileSystemEventHandler):
    """带防抖的文件变化处理器。"""

    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        src = event.src_path.replace("\\", "/")
        # 忽略 git 内部文件和临时文件
        if "/.git/" in src or src.endswith(".git"):
            return
        if src.endswith("~") or src.endswith(".tmp"):
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SECONDS, self._fire)
            self._timer.start()

    def _fire(self):
        if self._callback:
            self._callback()


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    print("=" * 58)
    print("  课程内容自动同步工具")
    print(f"  监听文件夹：{WATCH_DIR}")
    print(f"  防抖时间：{DEBOUNCE_SECONDS} 秒")
    print(f"  推送目标：{REMOTE} / {BRANCH}")
    print("  使用方法：直接编辑文件并保存，其余自动完成")
    print("  退出：关闭本窗口，或按 Ctrl+C")
    print("=" * 58)
    print()

    observer = Observer()
    handler = ChangeHandler(sync)
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
