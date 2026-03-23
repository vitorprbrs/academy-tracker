from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subject, Assessment
from app.schemas import SubjectCreate, SubjectUpdate, SubjectOut
from app.utils import (
    compute_current_average,
    compute_best_projection,
    compute_min_needed,
    compute_status,
)

router = APIRouter(prefix="/subjects", tags=["subjects"])


def enrich_subject(subject: Subject) -> SubjectOut:
    """Attach computed grade stats to a subject."""
    calc_type = subject.calc_type or "weighted"
    current = compute_current_average(subject.assessments, calc_type)
    projection = compute_best_projection(subject.assessments, calc_type)
    min_needed = compute_min_needed(subject.assessments, subject.passing_grade, calc_type)
    status = compute_status(subject.assessments, subject.passing_grade, current, projection)

    return SubjectOut(
        id=subject.id,
        name=subject.name,
        color=subject.color,
        passing_grade=subject.passing_grade,
        semester=subject.semester,
        calc_type=calc_type,
        assessments=subject.assessments,
        current_average=current,
        best_projection=projection,
        min_needed=min_needed,
        status=status,
    )


@router.get("/", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    return [enrich_subject(s) for s in subjects]


@router.post("/", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db)):
    if db.query(Subject).filter(Subject.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Matéria já existe com esse nome.")

    subject = Subject(
        name=payload.name,
        color=payload.color,
        passing_grade=payload.passing_grade,
        semester=payload.semester,
        calc_type=payload.calc_type,
    )
    db.add(subject)
    db.flush()  # get subject.id without committing

    for a in payload.assessments:
        db.add(Assessment(
            subject_id=subject.id,
            name=a.name,
            weight=a.weight,
            max_score=a.max_score,
            score=a.score,
        ))

    db.commit()
    db.refresh(subject)
    return enrich_subject(subject)


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")
    return enrich_subject(subject)


@router.put("/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)

    db.commit()
    db.refresh(subject)
    return enrich_subject(subject)


@router.delete("/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")
    db.delete(subject)
    db.commit()
