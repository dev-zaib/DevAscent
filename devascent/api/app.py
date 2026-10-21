"""DevAscent FastAPI application."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from devascent.api.routes import health, assessment, stream, coach, roadmap, learn, interview, tts, progress
from devascent.api.routes.health import ui_router, health_router

_ASSETS = Path(__file__).parent.parent.parent / "devascent_cli" / "web_dist" / "assets"

app = FastAPI(
    title="DevAscent Assessment API",
    description="Elite engineering assessment platform — production-grade skill evaluation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ui_router, tags=["ui"])
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(assessment.router, prefix="/api/assessment", tags=["assessment"])
app.include_router(stream.router, prefix="/api/assessment", tags=["stream"])
app.include_router(coach.router, prefix="/api/coach", tags=["coach"])
app.include_router(roadmap.router, prefix="/api/roadmap", tags=["roadmap"])
app.include_router(learn.router, prefix="/api/learn", tags=["learn"])
app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(tts.router, prefix="/api/tts", tags=["tts"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])

# Serve the built SPA's hashed JS/CSS bundles.
if _ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(_ASSETS)), name="assets")
