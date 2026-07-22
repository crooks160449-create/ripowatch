import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from git_manager import GitManager
from watcher import RepoWatcher

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
REPOS_DIR = BASE_DIR / "watched_repos"

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------
class AppState:
    def __init__(self):
        self.repos: dict[str, GitManager] = {}
        self.watcher = RepoWatcher()
        self.sse_queues: set[asyncio.Queue] = set()
        self.config = self._load_config()

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text("utf-8"))
            except Exception:
                pass
        return {"port": 8765, "host": "127.0.0.1", "debounce_seconds": 2}

    def notify(self, event_type, data):
        msg = json.dumps({"type": event_type, "data": data})
        stale = set()
        for q in self.sse_queues:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                stale.add(q)
        self.sse_queues -= stale


state = AppState()

# ---------------------------------------------------------------------------
# Demo / initialisation
# ---------------------------------------------------------------------------
def _create_demo_repo():
    """Create a demo Python project if no repos exist."""
    demo = REPOS_DIR / "demo-project"
    demo.mkdir(parents=True, exist_ok=True)

    (demo / "README.md").write_text("# Demo Project\n\nAuto-watched demo repository.\n")

    (demo / "main.py").write_text('''"""Demo Python project - Main entry point."""

from calculator import add, subtract, multiply, divide
from utils.helpers import greet, format_result


def main():
    name = greet("World")
    print(name)
    a, b = 42, 7
    print(f"{a} + {b} = {format_result(add(a, b))}")
    print(f"{a} - {b} = {format_result(subtract(a, b))}")
    print(f"{a} * {b} = {format_result(multiply(a, b))}")
    print(f"{a} / {b} = {format_result(divide(a, b))}")



if __name__ == "__main__":
    main()
''')

    (demo / "calculator.py").write_text('''"""Simple calculator module."""

import math


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b


def power(base: float, exp: float) -> float:
    return math.pow(base, exp)


def sqrt(x: float) -> float:
    if x < 0:
        raise ValueError("Cannot sqrt negative number")
    return math.sqrt(x)
''')

    utils = demo / "utils"
    utils.mkdir(exist_ok=True)
    (utils / "__init__.py").write_text("# utils package\n")
    (utils / "helpers.py").write_text('''"""Helper utilities."""

from datetime import datetime


def greet(name: str) -> str:
    hour = datetime.now().hour
    prefix = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    return f"{prefix}, {name}!"


def format_result(value: float) -> str:
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return f"{value:.2f}"
''')

    gm = GitManager(demo)
    gm.auto_commit("Initial demo setup")
    return gm


def init_repos():
    REPOS_DIR.mkdir(exist_ok=True)
    for item in sorted(REPOS_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            try:
                gm = GitManager(item)
                state.repos[item.name] = gm
            except Exception as exc:
                print(f"[warn] Failed to init repo '{item.name}': {exc}")
    if not state.repos:
        gm = _create_demo_repo()
        state.repos["demo-project"] = gm


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_repos()
    cfg = state.config
    for name, gm in state.repos.items():
        def _make_cb(n):
            def _cb(path):
                try:
                    mgr = state.repos.get(n)
                    if mgr and mgr.auto_commit():
                        info = mgr.get_repo_info()
                        state.notify("commit", {
                            "repo": n,
                            "message": (info["last_commit"]["message"]
                                        if info["last_commit"] else "Changes committed"),
                            "time": (info["last_commit"]["date_str"]
                                     if info["last_commit"] else ""),
                        })
                except Exception as exc:
                    print(f"[warn] auto-commit {n}: {exc}")
            return _cb
        state.watcher.add_watch(gm.repo_path, _make_cb(name), cfg.get("debounce_seconds", 2))
    state.watcher.start()
    yield
    state.watcher.stop()


app = FastAPI(title="RepoWatch", lifespan=lifespan)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

LANG_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".html": "html", ".css": "css", ".json": "json",
    ".md": "markdown", ".yaml": "yaml", ".yml": "yaml",
    ".sh": "bash", ".bat": "bat", ".txt": "text",
    ".c": "c", ".cpp": "cpp", ".h": "c",
    ".java": "java", ".rs": "rust", ".go": "go",
    ".rb": "ruby", ".php": "php", ".sql": "sql",
    ".xml": "xml", ".toml": "toml", ".ini": "ini",
    ".cfg": "ini", ".env": "bash", ".gitignore": "text", ".docx": "docx",
    ".dockerfile": "dockerfile", ".vue": "html",
}


# ---------------------------------------------------------------------------
# HTML routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    infos = []
    for name, gm in state.repos.items():
        try:
            infos.append(gm.get_repo_info())
        except Exception:
            infos.append({"name": name, "status": "error"})
    return templates.TemplateResponse(request, "repos.html", {"repos": infos})


@app.get("/repos/{name}", response_class=HTMLResponse)
async def repo_detail(name: str, request: Request):
    if name not in state.repos:
        raise HTTPException(404, f"Repo '{name}' not found")
    gm = state.repos[name]
    info = gm.get_repo_info()
    tree = gm.get_file_tree()
    return templates.TemplateResponse(request, "repo.html", {
        "request": request, "repo": info, "tree": json.dumps(tree),
    })


@app.get("/repos/{name}/file/{path:path}", response_class=HTMLResponse)
async def file_view(name: str, path: str, request: Request):
    if name not in state.repos:
        raise HTTPException(404, f"Repo '{name}' not found")
    gm = state.repos[name]
    ext = Path(path).suffix.lower()

    # PDF viewer
    if ext == ".pdf":
        info = gm.get_repo_info()
        tree = gm.get_file_tree()
        return templates.TemplateResponse(request, "pdf.html", {
            "request": request,
            "repo": info,
            "tree": json.dumps(tree),
            "file_path": path,
            "file_name": Path(path).name,
        })

    # PPTX viewer
    if ext == ".pptx":
        info = gm.get_repo_info()
        tree = gm.get_file_tree()
        slides = gm.get_pptx_content(path)
        return templates.TemplateResponse(request, "ppt.html", {
            "request": request,
            "repo": info,
            "tree": json.dumps(tree),
            "file_path": path,
            "file_name": Path(path).name,
            "slides": slides or [],
        })

    # DOCX viewer
    if ext == ".docx":
        info = gm.get_repo_info()
        tree = gm.get_file_tree()
        docx_content = gm.get_docx_content(path)
        return templates.TemplateResponse(request, "docx.html", {
            "request": request,
            "repo": info,
            "tree": json.dumps(tree),
            "file_path": path,
            "file_name": Path(path).name,
            "elements": docx_content or [],
        })

    content = gm.get_file_content(path)
    if content is None:
        raise HTTPException(404, f"File not found: {path}")
    ext = Path(path).suffix.lower()
    lang = LANG_MAP.get(ext, "plaintext")
    info = gm.get_repo_info()
    tree = gm.get_file_tree()
    return templates.TemplateResponse(request, "file.html", {
        "request": request,
        "repo": info,
        "tree": json.dumps(tree),
        "file_path": path,
        "file_content": content,
        "file_language": lang,
        "file_name": Path(path).name,
    })


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------
@app.get("/api/repos")
async def api_repos():
    return {n: mgr.get_repo_info() for n, mgr in state.repos.items()}


@app.get("/api/repos/{name}/commits")
async def api_commits(name: str):
    if name not in state.repos:
        raise HTTPException(404, f"Repo '{name}' not found")
    return state.repos[name].get_commits()


# ---------------------------------------------------------------------------
# SSE (real-time notifications)
# ---------------------------------------------------------------------------
@app.get("/events")
async def sse_stream(request: Request):
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    state.sse_queues.add(queue)

    async def _gen():
        try:
            yield "data: {\"type\":\"connected\"}\n\n"
            while True:
                msg = await queue.get()
                yield f"data: {msg}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            state.sse_queues.discard(queue)

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@app.get("/repos/{name}/raw/{path:path}")
async def raw_file(name: str, path: str):
    """Serve raw binary files (for PDF embedding etc.)."""
    if name not in state.repos:
        raise HTTPException(404)
    gm = state.repos[name]
    full_path = gm.repo_path / path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(404)
    ext = full_path.suffix.lower()
    media_map = {".pdf": "application/pdf", ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    media_type = media_map.get(ext, "application/octet-stream")
    headers = {}
    if ext == ".pdf":
        headers["Content-Disposition"] = "inline"
    return FileResponse(str(full_path), media_type=media_type, headers=headers)

if __name__ == "__main__":
    import uvicorn
    cfg = state.config
    port = cfg.get("port", 8765)
    host = cfg.get("host", "127.0.0.1")
    print(f"  RepoWatch started at http://{host}:{port}")
    print(f"  Watching {len(state.repos)} repos")
    uvicorn.run("main:app", host=host, port=port, reload=False, log_level="info")
