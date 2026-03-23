from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assessment, Subject
from app.schemas import AssessmentCreate, AssessmentUpdate, AssessmentOut

router = APIRouter(prefix="/subjects/{subject_id}/assessments", tags=["assessments"])


@router.get("/", response_model=list[AssessmentOut])
def list_assessments(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")
    return subject.assessments


@router.post("/", response_model=AssessmentOut, status_code=201)
def create_assessment(
    subject_id: int, payload: AssessmentCreate, db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")

    assessment = Assessment(subject_id=subject_id, **payload.model_dump())
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


# ─── Assessment-level operations (no subject prefix needed) ──────────────────

score_router = APIRouter(prefix="/assessments", tags=["assessments"])


@score_router.put("/{assessment_id}", response_model=AssessmentOut)
def update_assessment(
    assessment_id: int, payload: AssessmentUpdate, db: Session = Depends(get_db)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(assessment, field, value)

    db.commit()
    db.refresh(assessment)
    return assessment


@score_router.delete("/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    db.delete(assessment)
    db.commit()
