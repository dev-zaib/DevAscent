"""Health check and UI serving."""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui_router = APIRouter(tags=["ui"])
health_router = APIRouter(tags=["health"])

_REPO = Path(__file__).parent.parent.parent.parent
_DIST = _REPO / "devascent_cli" / "web_dist"
_LEGACY = _REPO / "web" / "public" / "assess.html"

_SPA: str | None = None
_CLASSIC: str | None = None


def _spa() -> str:
    """Built React SPA (Path-to-Top-1% studio). Falls back to legacy HTML."""
    global _SPA
    if _SPA is None:
        spa = _DIST / "devascent.html"
        if spa.exists():
            _SPA = spa.read_text(encoding="utf-8")
        elif _LEGACY.exists():
            _SPA = _LEGACY.read_text(encoding="utf-8")
        else:
            _SPA = "<h1>DevAscent</h1><p>Run <code>cd web && npm run build</code> to build the UI.</p>"
    return _SPA


def _classic() -> str:
    global _CLASSIC
    if _CLASSIC is None:
        _CLASSIC = _LEGACY.read_text(encoding="utf-8") if _LEGACY.exists() else _spa()
    return _CLASSIC


@ui_router.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=_spa())


@ui_router.get("/classic", response_class=HTMLResponse)
async def classic():
    """The original single-file assessment workspace."""
    return HTMLResponse(content=_classic())


@ui_router.get("/assess/{session_id}", response_class=HTMLResponse)
async def assess_page(session_id: str):
    return HTMLResponse(content=_spa())


@health_router.get("/health")
async def health_check():
    return {"status": "ok"}
