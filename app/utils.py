from typing import Optional
from app.models import Assessment


def compute_current_average(assessments: list[Assessment], calc_type: str = "weighted") -> Optional[float]:
    graded = [a for a in assessments if a.score is not None]
    if not graded:
        return None
    if calc_type == "simple":
        return round(sum(a.score for a in graded) / len(graded), 2)
    total_weight = sum(a.weight for a in graded)
    if total_weight == 0:
        return None
    return round(sum(a.score * a.weight for a in graded) / total_weight, 2)


def compute_best_projection(assessments: list[Assessment], calc_type: str = "weighted") -> Optional[float]:
    if not assessments:
        return None
    if calc_type == "simple":
        n = len(assessments)
        graded_sum = sum(a.score for a in assessments if a.score is not None)
        ungraded_max_sum = sum(a.max_score for a in assessments if a.score is None)
        return round((graded_sum + ungraded_max_sum) / n, 2)
    total_weight = sum(a.weight for a in assessments)
    if total_weight == 0:
        return None
    graded_sum = sum(a.score * a.weight for a in assessments if a.score is not None)
    ungraded_max = sum(a.max_score * a.weight for a in assessments if a.score is None)
    return round((graded_sum + ungraded_max) / total_weight, 2)


def compute_min_needed(
    assessments: list[Assessment], passing_grade: float, calc_type: str = "weighted"
) -> Optional[float]:
    ungraded = [a for a in assessments if a.score is None]
    if not ungraded:
        return None
    if calc_type == "simple":
        n = len(assessments)
        graded_sum = sum(a.score for a in assessments if a.score is not None)
        ungraded_count = len(ungraded)
        needed = (passing_grade * n - graded_sum) / ungraded_count
        return round(needed, 2)
    total_weight = sum(a.weight for a in assessments)
    if total_weight == 0:
        return None
    graded_contribution = sum(
        a.score * a.weight for a in assessments if a.score is not None
    )
    ungraded_weight = sum(a.weight for a in ungraded)
    needed = (passing_grade * total_weight - graded_contribution) / ungraded_weight
    return round(needed, 2)


def compute_status(
    assessments: list[Assessment],
    passing_grade: float,
    current_average: Optional[float],
    best_projection: Optional[float],
) -> str:
    if not assessments:
        return "pending"

    all_graded = all(a.score is not None for a in assessments)

    if current_average is None:
        return "pending"

    if all_graded:
        return "approved" if current_average >= passing_grade else "failed"

    if best_projection is not None and best_projection < passing_grade:
        return "failing"

    if current_average >= passing_grade:
        return "passing"

    return "pending"
