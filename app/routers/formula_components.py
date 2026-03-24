from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assessment, FormulaComponent, Subject
from app.schemas import (
    AssessmentCreate,
    AssessmentOut,
    FormulaComponentCreate,
    FormulaComponentOut,
    FormulaComponentUpdate,
)
from app.utils import _component_current_value

router = APIRouter(tags=["formula_components"])


def _enrich_component(c: FormulaComponent) -> FormulaComponentOut:
    val = _component_current_value(c.assessments, c.calc)
    return FormulaComponentOut(
        id=c.id,
        variable=c.variable,
        weight=c.weight,
        calc=c.calc,
        display_order=c.display_order,
        assessments=c.assessments,
        current_value=round(val, 2) if val is not None else None,
    )


# ─── Subject-scoped: list / create components ──────────────────────────────────

@router.get("/subjects/{subject_id}/formula-components", response_model=list[FormulaComponentOut])
def list_formula_components(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")
    return [_enrich_component(c) for c in subject.formula_components]


@router.post("/subjects/{subject_id}/formula-components", response_model=FormulaComponentOut, status_code=201)
def create_formula_component(
    subject_id: int, payload: FormulaComponentCreate, db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Matéria não encontrada.")

    component = FormulaComponent(
        subject_id=subject_id,
        variable=payload.variable,
        weight=payload.weight,
        calc=payload.calc,
        display_order=payload.display_order,
    )
    db.add(component)
    db.flush()

    for a in payload.assessments:
        db.add(Assessment(
            subject_id=subject_id,
            component_id=component.id,
            name=a.name,
            weight=a.weight,
            max_score=a.max_score,
            score=a.score,
        ))

    db.commit()
    db.refresh(component)
    return _enrich_component(component)


# ─── Component-level: update / delete ─────────────────────────────────────────

@router.put("/formula-components/{component_id}", response_model=FormulaComponentOut)
def update_formula_component(
    component_id: int, payload: FormulaComponentUpdate, db: Session = Depends(get_db)
):
    component = db.query(FormulaComponent).filter(FormulaComponent.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Componente não encontrado.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(component, field, value)

    db.commit()
    db.refresh(component)
    return _enrich_component(component)


@router.delete("/formula-components/{component_id}", status_code=204)
def delete_formula_component(component_id: int, db: Session = Depends(get_db)):
    component = db.query(FormulaComponent).filter(FormulaComponent.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Componente não encontrado.")
    db.delete(component)
    db.commit()


# ─── Assessments within a component ───────────────────────────────────────────

@router.post("/formula-components/{component_id}/assessments", response_model=AssessmentOut, status_code=201)
def add_assessment_to_component(
    component_id: int, payload: AssessmentCreate, db: Session = Depends(get_db)
):
    component = db.query(FormulaComponent).filter(FormulaComponent.id == component_id).first()
    if not component:
        raise HTTPException(status_code=404, detail="Componente não encontrado.")

    assessment = Assessment(
        subject_id=component.subject_id,
        component_id=component_id,
        name=payload.name,
        weight=payload.weight,
        max_score=payload.max_score,
        score=payload.score,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
