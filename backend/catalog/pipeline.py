from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .normalization import to_grams
from .schema import FoodItem, NutrientProfile, Portion, SourceInfo, VersionInfo
from .sources import load_sources
from .validation import validate_catalog
from .versioning import content_hash


def _build_key(name: str, brand: Optional[str], locale: str) -> str:
    key = f"{name.strip().lower()}::{(brand or '').strip().lower()}::{locale.strip().lower()}"
    return key


def _normalize_portions(portions: List[Dict[str, Any]]) -> List[Portion]:
    normalized: List[Portion] = []
    for portion in portions:
        unit = portion["unit"]
        amount = float(portion["amount"])
        gram_weight = float(portion.get("gram_weight", to_grams(amount, unit)))
        normalized.append(
            Portion(
                description=portion.get("description", "serving"),
                amount=amount,
                unit=unit,
                gram_weight=gram_weight,
            )
        )
    return normalized


def _to_float_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _nutrients_from_payload(payload: Dict[str, Any]) -> NutrientProfile:
    nutrients = payload["nutrients_per_100g"]
    return NutrientProfile(
        calories_kcal=_to_float_or_none(nutrients.get("calories_kcal")),
        protein_g=_to_float_or_none(nutrients.get("protein_g")),
        fat_g=_to_float_or_none(nutrients.get("fat_g")),
        carbs_g=_to_float_or_none(nutrients.get("carbs_g")),
        fiber_g=_to_float_or_none(nutrients.get("fiber_g")),
        sugar_g=_to_float_or_none(nutrients.get("sugar_g")),
        sodium_mg=_to_float_or_none(nutrients.get("sodium_mg")),
    )


def _serialize_item(item: FoodItem) -> Dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "brand": item.brand,
        "locale": item.locale,
        "confidence": item.confidence,
        "sources": [source.__dict__ for source in item.sources],
        "portions": [portion.__dict__ for portion in item.portions],
        "nutrients_per_100g": item.nutrients_per_100g.__dict__,
        "version": item.version.__dict__,
    }


def _merge_payload(
    existing: Optional[Dict[str, Any]],
    payload: Dict[str, Any],
    source: SourceInfo,
) -> Dict[str, Any]:
    nutrients = _nutrients_from_payload(payload)
    portions = _normalize_portions(payload["portions"])
    name = payload["name"]
    brand = payload.get("brand")
    locale = payload.get("locale", "en-US")
    confidence = float(payload.get("confidence", 0.8))

    if existing is None:
        return {
            "name": name,
            "brand": brand,
            "locale": locale,
            "confidence": confidence,
            "sources": {source.name: source},
            "portions": portions,
            "nutrients": nutrients,
            "primary_confidence": confidence,
        }

    existing_sources = existing["sources"]
    existing_sources[source.name] = source
    primary_confidence = existing.get("primary_confidence", existing["confidence"])
    if confidence >= primary_confidence:
        existing["portions"] = portions
        existing["nutrients"] = nutrients
        primary_confidence = confidence
    existing["confidence"] = max(existing["confidence"], confidence)
    existing["sources"] = existing_sources
    existing["primary_confidence"] = primary_confidence
    return existing


def _content_payload(item_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": item_data["name"],
        "brand": item_data["brand"],
        "locale": item_data["locale"],
        "confidence": item_data["confidence"],
        "portions": [portion.__dict__ for portion in item_data["portions"]],
        "nutrients_per_100g": item_data["nutrients"].__dict__,
    }


def load_existing_catalog(path: Path) -> Dict[str, FoodItem]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    items = {}
    for entry in data.get("items", []):
        item = FoodItem(
            id=entry["id"],
            name=entry["name"],
            brand=entry.get("brand"),
            locale=entry["locale"],
            confidence=entry["confidence"],
            sources=[SourceInfo(**source) for source in entry["sources"]],
            portions=[Portion(**portion) for portion in entry["portions"]],
            nutrients_per_100g=NutrientProfile(**entry["nutrients_per_100g"]),
            version=VersionInfo(**entry["version"]),
        )
        key = _build_key(item.name, item.brand, item.locale)
        items[key] = item
    return items


def ingest_sources(source_paths: List[Path], existing_path: Path) -> List[FoodItem]:
    source_payloads = load_sources(source_paths)
    existing = load_existing_catalog(existing_path)
    merged: Dict[str, Dict[str, Any]] = {}

    for payload in source_payloads:
        source_info = SourceInfo(**payload["source"])
        for item_payload in payload["items"]:
            key = _build_key(
                item_payload["name"],
                item_payload.get("brand"),
                item_payload.get("locale", "en-US"),
            )
            merged[key] = _merge_payload(merged.get(key), item_payload, source_info)

    catalog: List[FoodItem] = []
    for key, item_data in merged.items():
        hash_payload = _content_payload(item_data)
        new_hash = content_hash(hash_payload)
        if key in existing:
            existing_item = existing[key]
            revision = existing_item.version.revision
            if existing_item.version.content_hash != new_hash:
                revision += 1
            item_id = existing_item.id
        else:
            revision = 1
            item_id = str(uuid.uuid4())
        catalog.append(
            FoodItem(
                id=item_id,
                name=item_data["name"],
                brand=item_data["brand"],
                locale=item_data["locale"],
                confidence=item_data["confidence"],
                sources=list(item_data["sources"].values()),
                portions=item_data["portions"],
                nutrients_per_100g=item_data["nutrients"],
                version=VersionInfo(revision=revision, content_hash=new_hash),
            )
        )

    validate_catalog(catalog)
    return catalog


def write_catalog(items: List[FoodItem], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "items": [_serialize_item(item) for item in items],
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def run_import(source_paths: List[Path], output_path: Path) -> Tuple[int, Path]:
    catalog = ingest_sources(source_paths, output_path)
    write_catalog(catalog, output_path)
    return len(catalog), output_path
