from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .schema import FoodItem


@dataclass(frozen=True)
class ValidationIssue:
    item_id: str
    message: str
    severity: str


class ValidationError(ValueError):
    def __init__(self, issues: List[ValidationIssue]):
        super().__init__("Validation failed")
        self.issues = issues


MAX_CALORIES_PER_100G = 1000
MIN_MACRO_VALUE = 0


def validate_food_item(item: FoodItem) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    nutrients = item.nutrients_per_100g
    for macro_name, value in (
        ("protein_g", nutrients.protein_g),
        ("fat_g", nutrients.fat_g),
        ("carbs_g", nutrients.carbs_g),
    ):
        if value is None:
            issues.append(
                ValidationIssue(
                    item.id,
                    f"Missing macro nutrient: {macro_name}",
                    "error",
                )
            )
        elif value < MIN_MACRO_VALUE:
            issues.append(
                ValidationIssue(
                    item.id,
                    f"Negative macro nutrient: {macro_name}",
                    "error",
                )
            )
    if nutrients.calories_kcal is None:
        issues.append(
            ValidationIssue(item.id, "Missing calories", "error")
        )
    elif nutrients.calories_kcal > MAX_CALORIES_PER_100G:
        issues.append(
            ValidationIssue(
                item.id,
                f"Calories outlier (> {MAX_CALORIES_PER_100G} per 100g)",
                "warning",
            )
        )
    return issues


def validate_catalog(items: List[FoodItem]) -> None:
    issues: List[ValidationIssue] = []
    for item in items:
        issues.extend(validate_food_item(item))
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise ValidationError(issues)
