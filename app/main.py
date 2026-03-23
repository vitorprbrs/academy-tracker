from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from sqlalchemy import text
from app.database import Base, engine
from app.routers.subjects import router as subjects_router
from app.routers.assessments import router as assessments_router, score_router
from app.routers.events import router as events_router
from app.routers.insights import router as insights_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Migrate: add calc_type column if it doesn't exist (safe no-op if already present)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE subjects ADD COLUMN calc_type VARCHAR(10) DEFAULT 'weighted'"))
            conn.commit()
        except Exception:
            pass
    yield


app = FastAPI(
    title="Academic Tracker API",
    description="Sistema de acompanhamento acadêmico com IA local (Ollama)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routers ──────────────────────────────────────────────────────────────
app.include_router(subjects_router, prefix="/api")
app.include_router(assessments_router, prefix="/api")
app.include_router(score_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(insights_router, prefix="/api")


# ─── Serve Frontend ───────────────────────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
