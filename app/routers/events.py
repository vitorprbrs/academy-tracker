from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CalendarEvent, Subject
from app.schemas import EventCreate, EventUpdate, EventOut

router = APIRouter(prefix="/events", tags=["events"])


def enrich_event(event: CalendarEvent) -> EventOut:
    return EventOut(
        id=event.id,
        subject_id=event.subject_id,
        title=event.title,
        date=event.date,
        event_type=event.event_type,
        description=event.description,
        subject_name=event.subject.name if event.subject else None,
        subject_color=event.subject.color if event.subject else None,
    )


@router.get("/", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    events = db.query(CalendarEvent).order_by(CalendarEvent.date).all()
    return [enrich_event(e) for e in events]


@router.post("/", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    if payload.subject_id:
        subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Matéria não encontrada.")

    event = CalendarEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return enrich_event(event)


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return enrich_event(event)


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    db.delete(event)
    db.commit()
