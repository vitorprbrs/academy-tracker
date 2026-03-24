from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subject, Assessment, FormulaComponent
from app.schemas import SubjectCreate, SubjectUpdate, SubjectOut, FormulaComponentOut
from app.utils import (
    compute_current_average,
    compute_best_projection,
    compute_min_needed,
    compute_status,
    compute_formula_current_average,
    compute_formula_best_projection,
    compute_formula_min_needed,
    build_formula_string,
    _component_current_value,
)

router = APIRouter(prefix="/subjects", tags=["subjects"])


def enrich_subject(subject: Subject) -> SubjectOut:
    """Attach computed grade stats to a subject."""
    calc_type = subject.calc_type or "weighted"

    if calc_type == "formula":
        components = subject.formula_components
        current = compute_formula_current_average(components)
        projection = compute_formula_best_projection(components)
        min_needed = compute_formula_min_needed(components, subject.passing_grade)
        all_assessments = [a for c in components for a in c.assessments]
        status = compute_status(all_assessments, subject.passing_grade, current, projection)
        formula_str = build_formula_string(components)

        enriched_components = []
        for c in components:
            val = _component_current_value(c.assessments, c.calc)
            enriched_components.append(FormulaComponentOut(
                id=c.id,
                variable=c.variable,
                weight=c.weight,
                calc=c.calc,
                display_order=c.display_order,
                assessments=c.assessments,
                current_value=round(val, 2) if val is not None else None,
            ))

        return SubjectOut(
            id=subject.id,
            name=subject.name,
            color=subject.color,
            passing_grade=subject.passing_grade,
            semester=subject.semester,
            calc_type=calc_type,
            assessments=[],
            formula_components=enriched_components,
            formula_string=formula_str,
            current_average=current,
            best_projection=projection,
            min_needed=min_needed,
            status=status,
        )

    # simple / weighted
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
        formula_components=[],
        formula_string=None,
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
    db.flush()

    if payload.calc_type == "formula":
        for fc in payload.formula_components:
            component = FormulaComponent(
                subject_id=subject.id,
                variable=fc.variable,
                weight=fc.weight,
                calc=fc.calc,
                display_order=fc.display_order,
            )
            db.add(component)
            db.flush()
            for a in fc.assessments:
                db.add(Assessment(
                    subject_id=subject.id,
                    component_id=component.id,
                    name=a.name,
                    weight=a.weight,
                    max_score=a.max_score,
                    score=a.score,
                ))
    else:
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
