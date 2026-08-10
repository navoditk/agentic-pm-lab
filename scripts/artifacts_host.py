"""Runtime Layer: local, non-prod artifact host.

Serves anything dropped into artifacts/ — generated single-file HTML+JS
reports, mainly. Not the production path (that's Day 11); this is just a
quick local way to view what an agent produces. Run with:

    uv run python scripts/artifacts_host.py
"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "artifacts"

app = FastAPI(title="artifacts_host")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    files = sorted(p.name for p in ARTIFACTS_DIR.iterdir() if p.is_file())
    links = "\n".join(f'<li><a href="/files/{name}">{name}</a></li>' for name in files)
    return f"<h1>artifacts/</h1><ul>{links}</ul>"


app.mount("/files", StaticFiles(directory=ARTIFACTS_DIR), name="files")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
