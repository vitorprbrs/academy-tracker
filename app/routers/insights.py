import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import SessionLocal
from app.models import Subject, CalendarEvent
from app.schemas import InsightRequest
from app.routers.subjects import enrich_subject
from app.routers.events import enrich_event
from app.ai.agent import stream_insights, stream_insights_auto, stream_subject_insight, stream_subject_insight_auto

router = APIRouter(prefix="/insights", tags=["insights"])

NO_DATA_MSG = (
    "Ainda não há dados suficientes para gerar insights. "
    "Insira algumas notas para obter uma análise personalizada."
)



def _count_scores(subjects_data: list) -> int:
    """Returns the total number of entered scores across all subjects."""
    count = 0
    for s in subjects_data:
        for a in s.get("assessments", []):
            if a.get("score") is not None:
                count += 1
        for comp in s.get("formula_components", []):
            for a in comp.get("assessments", []):
                if a.get("score") is not None:
                    count += 1
    return count


def _no_data_response():
    async def generate():
        yield f"data: {json.dumps({'text': NO_DATA_MSG})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _fetch_all_subjects_events():
    """Load subjects+events from DB synchronously (runs in a thread)."""
    db = SessionLocal()
    try:
        subjects = db.query(Subject).all()
        events = db.query(CalendarEvent).all()
        subjects_data = [enrich_subject(s).model_dump() for s in subjects]
        events_data = [enrich_event(e).model_dump() for e in events]
        return subjects_data, events_data
    finally:
        db.close()


def _fetch_subject(subject_id: int):
    """Load a single subject from DB synchronously (runs in a thread)."""
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if subject is None:
            return None
        return enrich_subject(subject).model_dump()
    finally:
        db.close()


@router.post("/stream")
async def insights_stream(payload: InsightRequest):
    subjects_data, events_data = await asyncio.to_thread(_fetch_all_subjects_events)

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
async def auto_insight_stream():
    """Dashboard auto-insight: OpenAI first → Ollama fallback."""
    subjects_data, events_data = await asyncio.to_thread(_fetch_all_subjects_events)

    if _count_scores(subjects_data) == 0:
        return _no_data_response()

    async def generate():
        try:
            async for chunk in stream_insights_auto(subjects_data, events_data):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/subject/{subject_id}/stream")
async def subject_insight_stream(subject_id: int):
    """Subject-specific auto-insight: focused analysis of a single subject."""
    subject_data = await asyncio.to_thread(_fetch_subject, subject_id)
    if subject_data is None:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")

    if _count_scores([subject_data]) == 0:
        return _no_data_response()

    async def generate():
        try:
            async for chunk in stream_subject_insight_auto(subject_data):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
