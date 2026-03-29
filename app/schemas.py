from pydantic import BaseModel, Field
from typing import Optional


class AssessmentCreate(BaseModel):
    name: str
    weight: float = Field(default=1.0, gt=0)
    max_score: float = Field(default=10.0, gt=0)
    score: Optional[float] = None


class AssessmentUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = Field(default=None, gt=0)
    max_score: Optional[float] = Field(default=None, gt=0)
    score: Optional[float] = None
    component_id: Optional[int] = None


class AssessmentOut(BaseModel):
    id: int
    subject_id: int
    component_id: Optional[int] = None
    name: str
    weight: float
    max_score: float
    score: Optional[float]

    model_config = {"from_attributes": True}


# ─── Formula Component Schemas ─────────────────────────────────────────────────

class FormulaComponentCreate(BaseModel):
    variable: str
    weight: float = Field(gt=0)
    calc: str = "simple"            # "simple" | "weighted"
    display_order: int = 0
    assessments: list[AssessmentCreate] = []


class FormulaComponentUpdate(BaseModel):
    variable: Optional[str] = None
    weight: Optional[float] = Field(default=None, gt=0)
    calc: Optional[str] = None
    display_order: Optional[int] = None


class FormulaComponentOut(BaseModel):
    id: int
    variable: str
    weight: float
    calc: str
    display_order: int
    assessments: list[AssessmentOut] = []
    current_value: Optional[float] = None   # computed average for this component

    model_config = {"from_attributes": True}


# ─── Subject Schemas ───────────────────────────────────────────────────────────

class SubjectCreate(BaseModel):
    name: str
    color: str = "#6366f1"
    passing_grade: float = Field(default=6.0, ge=0)
    semester: Optional[str] = None
    calc_type: str = "weighted"
    assessments: list[AssessmentCreate] = []
    formula_components: list[FormulaComponentCreate] = []


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    passing_grade: Optional[float] = Field(default=None, ge=0)
    semester: Optional[str] = None
    calc_type: Optional[str] = None
    assessments: Optional[list[AssessmentCreate]] = None
    formula_components: Optional[list[FormulaComponentCreate]] = None


class SubjectOut(BaseModel):
    id: int
    name: str
    color: str
    passing_grade: float
    semester: Optional[str]
    calc_type: str = "weighted"
    assessments: list[AssessmentOut] = []
    formula_components: list[FormulaComponentOut] = []
    formula_string: Optional[str] = None   # "MF = 0,7 × NT + 0,3 × SF"
    current_average: Optional[float] = None
    best_projection: Optional[float] = None
    min_needed: Optional[float] = None
    status: str = "pending"

    model_config = {"from_attributes": True}


# ─── Event Schemas ─────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    subject_id: Optional[int] = None
    title: str
    date: str
    event_type: str = "exam"
    description: Optional[str] = None


class EventUpdate(BaseModel):
    subject_id: Optional[int] = None
    title: Optional[str] = None
    date: Optional[str] = None
    event_type: Optional[str] = None
    description: Optional[str] = None


class EventOut(BaseModel):
    id: int
    subject_id: Optional[int]
    title: str
    date: str
    event_type: str
    description: Optional[str]
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None

    model_config = {"from_attributes": True}


class InsightRequest(BaseModel):
    provider: str = "ollama"          # "ollama" | "openai"
    model: str = "llama3.2"
    openai_api_key: Optional[str] = None
    focus: Optional[str] = None
