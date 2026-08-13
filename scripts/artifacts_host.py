"""Runtime Layer: local, non-prod artifact host.

Serves anything dropped into artifacts/ — generated single-file HTML+JS
reports, mainly. Not the production path (that's Day 11); this is just a
quick local way to view what an agent produces. Run with:

    uv run python scripts/artifacts_host.py
"""

from datetime import UTC, datetime
from html import escape
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


@app.post("/generate/risk-summary")
def generate_risk_summary() -> dict[str, str]:
    """Write a self-contained, clearly labelled portfolio risk report."""
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    filename = "portfolio-risk-summary.html"
    rows = [
        ("Market value", "$1.25m", "mock holdings"),
        ("Annualized volatility", "12.3%", "deterministic risk fixture"),
        ("Maximum drawdown", "-7.4%", "deterministic risk fixture"),
        ("Largest position", "31.0%", "mock security master"),
    ]
    table_rows = "".join(
        f"<tr><td>{escape(label)}</td><td>{escape(value)}</td><td>{escape(note)}</td></tr>"
        for label, value, note in rows
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Portfolio Risk Summary</title>
<style>body{{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px;color:#17202a}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccd;padding:10px;text-align:left}}.notice{{background:#fff3cd;padding:12px;border-radius:6px}}</style>
</head><body><h1>Portfolio Risk Summary</h1>
<p class="notice"><strong>Learning artifact:</strong> public/mock fixture only; not investment advice or a trading instruction.</p>
<p>Generated at {escape(generated_at)}. The report demonstrates the local artifact-host path and records provenance beside each metric.</p>
<table><thead><tr><th>Metric</th><th>Value</th><th>Provenance</th></tr></thead><tbody>{table_rows}</tbody></table>
<h2>Review questions</h2><ul><li>Refresh holdings and security classifications before relying on concentration.</li><li>Confirm the curve observation date and scenario assumptions.</li><li>Obtain human approval before any allocation change.</li></ul>
</body></html>"""
    (ARTIFACTS_DIR / filename).write_text(html)
    return {
        "filename": filename,
        "url": f"/files/{filename}",
        "generated_at": generated_at,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
