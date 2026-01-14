from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class SourceInfo:
    name: str
    dataset: str
    version: str
    url: Optional[str] = None


@dataclass(frozen=True)
class Portion:
    description: str
    amount: float
    unit: str
    gram_weight: float


@dataclass(frozen=True)
class NutrientProfile:
    calories_kcal: Optional[float]
    protein_g: Optional[float]
    fat_g: Optional[float]
    carbs_g: Optional[float]
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None


@dataclass(frozen=True)
class VersionInfo:
    revision: int
    content_hash: str
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class FoodItem:
    id: str
    name: str
    brand: Optional[str]
    locale: str
    confidence: float
    sources: List[SourceInfo]
    portions: List[Portion]
    nutrients_per_100g: NutrientProfile
    version: VersionInfo
