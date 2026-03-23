import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Subject, CalendarEvent
from app.schemas import InsightRequest
from app.routers.subjects import enrich_subject
from app.routers.events import enrich_event
from app.ai.agent import stream_insights, stream_subject_insight

router = APIRouter(prefix="/insights", tags=["insights"])


def _auto_provider_model():
    """Selects provider/model from .env settings automatically."""
    return "openai", settings.openai_default_model, settings.openai_api_key
    # return "ollama", settings.ollama_default_model, None


@router.post("/stream")
async def insights_stream(payload: InsightRequest, db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    events = db.query(CalendarEvent).all()
    subjects_data = [enrich_subject(s).model_dump() for s in subjects]
    events_data = [enrich_event(e).model_dump() for e in events]

    async def generate():
        try:
            async for chunk in stream_insights(
                subjects_data,
                events_data,
                provider=payload.provider,
                model=payload.model,
                openai_api_key=payload.openai_api_key,
                focus=payload.focus,
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/auto/stream")
async def auto_insight_stream(db: Session = Depends(get_db)):
    """Dashboard auto-insight: uses all subjects + events, provider from .env."""
    subjects = db.query(Subject).all()
    events = db.query(CalendarEvent).all()
    subjects_data = [enrich_subject(s).model_dump() for s in subjects]
    events_data = [enrich_event(e).model_dump() for e in events]
    provider, model, api_key = _auto_provider_model()

    async def generate():
        try:
            async for chunk in stream_insights(
                subjects_data, events_data,
                provider=provider, model=model, openai_api_key=api_key,
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/subject/{subject_id}/stream")
async def subject_insight_stream(subject_id: int, db: Session = Depends(get_db)):
    """Subject-specific auto-insight: focused analysis of a single subject."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")
    subject_data = enrich_subject(subject).model_dump()
    provider, model, api_key = _auto_provider_model()

    async def generate():
        try:
            async for chunk in stream_subject_insight(
                subject_data, provider=provider, model=model, openai_api_key=api_key,
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
