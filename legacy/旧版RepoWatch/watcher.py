import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class _ChangeHandler(FileSystemEventHandler):
    """Debounced handler that triggers a callback after files stop changing."""

    def __init__(self, repo_path, callback, debounce_seconds):
        self._repo_path = str(Path(repo_path).resolve())
        self._callback = callback
        self._debounce = debounce_seconds
        self._timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        if event.is_directory:
            return
        src = event.src_path.replace("\\", "/")
        if "/.git/" in src or src.endswith(".git"):
            return
        if src.endswith("~") or src.endswith(".tmp"):
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._fire)
            self._timer.start()

    def _fire(self):
        if self._callback:
            self._callback(self._repo_path)


class RepoWatcher:
    """Watch directories for changes and trigger auto-commits."""

    def __init__(self):
        self._observer = Observer()
        self._watches = {}
        self._running = False

    def add_watch(self, repo_path, callback, debounce_seconds=2):
        path = str(Path(repo_path).resolve())
        if path in self._watches:
            return
        handler = _ChangeHandler(path, callback, debounce_seconds)
        watch = self._observer.schedule(handler, path, recursive=True)
        self._watches[path] = watch

    def remove_watch(self, repo_path):
        path = str(Path(repo_path).resolve())
        if path in self._watches:
            self._observer.unschedule(self._watches.pop(path))

    def start(self):
        if not self._running:
            self._observer.start()
            self._running = True

    def stop(self):
        if self._running:
            self._observer.stop()
            self._observer.join()
            self._running = False
