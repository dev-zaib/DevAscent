"""DevAscent FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from devascent.api.routes import health, assessment, stream

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

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(assessment.router, prefix="/api/assessment", tags=["assessment"])
app.include_router(stream.router, prefix="/api/assessment", tags=["stream"])
