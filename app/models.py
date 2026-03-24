from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), default="#6366f1")        # hex color
    passing_grade = Column(Float, default=6.0)
    semester = Column(String(20), nullable=True)        # ex: "2024.2"

    calc_type = Column(String(10), default="weighted", server_default="weighted")  # "simple" | "weighted" | "formula"

    assessments = relationship(
        "Assessment", back_populates="subject", cascade="all, delete-orphan"
    )
    events = relationship(
        "CalendarEvent", back_populates="subject", cascade="all, delete-orphan"
    )
    formula_components = relationship(
        "FormulaComponent",
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="FormulaComponent.display_order",
    )


class FormulaComponent(Base):
    __tablename__ = "formula_components"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    variable = Column(String(20), nullable=False)       # ex: "NT", "SF"
    weight = Column(Float, nullable=False)              # ex: 0.7, 0.3
    calc = Column(String(10), default="simple")         # "simple" | "weighted"
    display_order = Column(Integer, default=0)

    subject = relationship("Subject", back_populates="formula_components")
    assessments = relationship(
        "Assessment",
        back_populates="component",
        cascade="all, delete-orphan",
        order_by="Assessment.id",
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("formula_components.id"), nullable=True)
    name = Column(String(100), nullable=False)          # ex: "Prova 1", "Trabalho Final"
    weight = Column(Float, default=1.0)                  # peso relativo
    max_score = Column(Float, default=10.0)              # nota máxima possível
    score = Column(Float, nullable=True)                 # None = ainda não realizado

    subject = relationship("Subject", back_populates="assessments")
    component = relationship("FormulaComponent", back_populates="assessments")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    title = Column(String(150), nullable=False)
    date = Column(String(10), nullable=False)            # ISO format: YYYY-MM-DD
    event_type = Column(String(20), default="exam")     # exam | activity | deadline | other
    description = Column(Text, nullable=True)

    subject = relationship("Subject", back_populates="events")
