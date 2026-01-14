from pathlib import Path

import pytest

from backend.catalog.pipeline import ingest_sources, run_import
from backend.catalog.validation import ValidationError


def test_ingest_dedup_and_versioning(tmp_path: Path) -> None:
    output_path = tmp_path / "catalog.json"
    sources = [
        Path("backend/catalog/data/source_usda.json"),
        Path("backend/catalog/data/source_brand.json"),
    ]
    catalog = ingest_sources(sources, output_path)

    banana = [item for item in catalog if item.name == "Banana"]
    assert len(banana) == 1
    assert banana[0].version.revision == 1

    # Re-import with existing catalog should keep revision stable
    run_import(sources, output_path)
    catalog_again = ingest_sources(sources, output_path)
    banana_again = [item for item in catalog_again if item.name == "Banana"][0]
    assert banana_again.version.revision == 1


def test_unit_normalization_for_ml(tmp_path: Path) -> None:
    output_path = tmp_path / "catalog.json"
    sources = [Path("backend/catalog/data/source_brand.json")]
    catalog = ingest_sources(sources, output_path)
    oat_milk = [item for item in catalog if item.name == "Oat Milk"][0]
    portion = oat_milk.portions[0]
    assert portion.unit == "ml"
    assert portion.gram_weight == pytest.approx(240.0)


def test_validation_missing_macros(tmp_path: Path) -> None:
    output_path = tmp_path / "catalog.json"
    broken_source = tmp_path / "broken.json"
    broken_source.write_text(
        """
        {
          "source": {
            "name": "Broken",
            "dataset": "Test",
            "version": "1",
            "url": null
          },
          "items": [
            {
              "name": "Bad Food",
              "locale": "en-US",
              "portions": [
                {"description": "100g", "amount": 100, "unit": "g"}
              ],
              "nutrients_per_100g": {
                "calories_kcal": 50,
                "protein_g": 1,
                "fat_g": 1,
                "carbs_g": null
              }
            }
          ]
        }
        """
    )
    with pytest.raises(ValidationError) as excinfo:
        ingest_sources([broken_source], output_path)

    assert any("Missing macro nutrient" in issue.message for issue in excinfo.value.issues)
