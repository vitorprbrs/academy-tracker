from typing import Optional
from app.models import Assessment


# ─── Simple / Weighted calculations ───────────────────────────────────────────

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


# ─── Formula calculations ──────────────────────────────────────────────────────

def _component_current_value(assessments: list[Assessment], calc: str = "simple") -> Optional[float]:
    """Average for a formula component from its graded assessments only."""
    graded = [a for a in assessments if a.score is not None]
    if not graded:
        return None
    if calc == "simple":
        return sum(a.score for a in graded) / len(graded)
    # weighted
    total_w = sum(a.weight for a in graded)
    if total_w == 0:
        return None
    return sum(a.score * a.weight for a in graded) / total_w


def compute_formula_current_average(components) -> Optional[float]:
    """
    MF = Σ(comp.weight × comp_avg), renormalized by the sum of graded-component weights.
    E.g. if only NT (weight 0.7) is graded: current average = NT_avg (not 0.7 × NT_avg).
    """
    graded_pairs = []
    for c in components:
        val = _component_current_value(c.assessments, c.calc)
        if val is not None:
            graded_pairs.append((c.weight, val))

    if not graded_pairs:
        return None

    total_graded_weight = sum(w for w, _ in graded_pairs)
    if total_graded_weight == 0:
        return None

    weighted_sum = sum(w * v for w, v in graded_pairs)
    return round(weighted_sum / total_graded_weight, 2)


def compute_formula_best_projection(components) -> Optional[float]:
    """Best case: all pending assessments score their maximum."""
    if not components:
        return None

    full_weight = sum(c.weight for c in components)
    if full_weight == 0:
        return None

    total = 0.0
    for c in components:
        all_a = c.assessments
        if not all_a:
            continue
        if c.calc == "simple":
            n = len(all_a)
            graded_sum = sum(a.score for a in all_a if a.score is not None)
            ungraded_max = sum(a.max_score for a in all_a if a.score is None)
            comp_best = (graded_sum + ungraded_max) / n
        else:
            total_w = sum(a.weight for a in all_a)
            if total_w == 0:
                continue
            graded_sum = sum(a.score * a.weight for a in all_a if a.score is not None)
            ungraded_max = sum(a.max_score * a.weight for a in all_a if a.score is None)
            comp_best = (graded_sum + ungraded_max) / total_w
        total += c.weight * comp_best

    return round(total / full_weight, 2)


def compute_formula_min_needed(components, passing_grade: float) -> Optional[float]:
    """
    Solve for uniform score x such that MF(x) = passing_grade, where all pending
    assessments get x.  Uses linear algebra: MF(x) = constant + coeff * x = passing_grade.
    """
    any_ungraded = any(a.score is None for c in components for a in c.assessments)
    if not any_ungraded:
        return None

    full_weight = sum(c.weight for c in components)
    if full_weight == 0:
        return None

    constant_sum = 0.0
    coeff_sum = 0.0

    for c in components:
        graded = [a for a in c.assessments if a.score is not None]
        ungraded = [a for a in c.assessments if a.score is None]

        if not ungraded:
            # Fully graded component — fixed contribution
            val = _component_current_value(c.assessments, c.calc)
            if val is not None:
                constant_sum += c.weight * val
            continue

        if c.calc == "simple":
            n = len(c.assessments)
            if n == 0:
                continue
            graded_sum = sum(a.score for a in graded)
            # comp_value(x) = (graded_sum + len(ungraded) * x) / n
            constant_sum += c.weight * graded_sum / n
            coeff_sum += c.weight * len(ungraded) / n
        else:
            total_w = sum(a.weight for a in c.assessments)
            if total_w == 0:
                continue
            graded_contrib = sum(a.score * a.weight for a in graded)
            ungraded_w = sum(a.weight for a in ungraded)
            # comp_value(x) = (graded_contrib + ungraded_w * x) / total_w
            constant_sum += c.weight * graded_contrib / total_w
            coeff_sum += c.weight * ungraded_w / total_w

    if coeff_sum == 0:
        return None

    needed = (passing_grade * full_weight - constant_sum) / coeff_sum
    return round(needed, 2)


def build_formula_string(components) -> str:
    """Generate display string: 'MF = 0,7 × NT + 0,3 × SF'"""
    if not components:
        return ""
    parts = []
    for c in sorted(components, key=lambda x: x.display_order):
        weight_str = f"{c.weight:g}".replace(".", ",")
        parts.append(f"{weight_str} × {c.variable}")
    return "MF = " + " + ".join(parts)
