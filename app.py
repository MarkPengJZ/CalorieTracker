from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")


@dataclass
class FoodItem:
    id: str
    name: str
    calories: int
    protein: int
    carbs: int
    fat: int
    popularity: float
    source: str = "catalog"


FOODS: list[FoodItem] = [
    FoodItem("1", "Greek Yogurt", 100, 17, 6, 0, 0.85),
    FoodItem("2", "Chicken Breast", 165, 31, 0, 3, 0.92),
    FoodItem("3", "Oatmeal", 150, 5, 27, 3, 0.78),
    FoodItem("4", "Avocado Toast", 240, 6, 24, 14, 0.67),
    FoodItem("5", "Protein Shake", 220, 30, 8, 4, 0.88),
]

user_history: dict[str, dict[str, int]] = {}
user_favorites: dict[str, set[str]] = {}
user_recents: dict[str, list[str]] = {}
custom_macros: dict[str, list[FoodItem]] = {}
meal_templates: dict[str, list[dict[str, Any]]] = {}

CACHE_TTL = 30
CACHE_MAX = 50
search_cache: dict[tuple[str, str], dict[str, Any]] = {}
query_counts: dict[tuple[str, str], int] = {}


@app.route("/")
def index() -> Any:
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/search")
def search() -> Any:
    query = request.args.get("q", "").strip()
    user_id = request.args.get("user_id", "default")
    if not query:
        return jsonify({"results": [], "cached": False})

    cache_key = (user_id, query.lower())
    cached = get_cached_results(cache_key)
    if cached is not None:
        return jsonify({"results": cached, "cached": True})

    candidates = list(FOODS)
    candidates.extend(custom_macros.get(user_id, []))

    history_counts = user_history.get(user_id, {})
    max_history = max(history_counts.values(), default=0)
    max_popularity = max((item.popularity for item in candidates), default=1)

    ranked = []
    for item in candidates:
        text_score = text_match_score(item.name, query)
        if text_score == 0:
            continue
        popularity_score = item.popularity / max_popularity
        history_score = (
            history_counts.get(item.id, 0) / max_history if max_history else 0
        )
        score = round((0.6 * text_score) + (0.25 * popularity_score) + (0.15 * history_score), 4)
        ranked.append({
            "id": item.id,
            "name": item.name,
            "calories": item.calories,
            "protein": item.protein,
            "carbs": item.carbs,
            "fat": item.fat,
            "popularity": item.popularity,
            "source": item.source,
            "score": score,
        })

    ranked.sort(key=lambda r: r["score"], reverse=True)

    store_cached_results(cache_key, ranked)
    return jsonify({"results": ranked, "cached": False})


@app.route("/api/log", methods=["POST"])
def log_entry() -> Any:
    payload = request.get_json(force=True)
    item_id = payload.get("item_id")
    user_id = payload.get("user_id", "default")
    if not item_id:
        return jsonify({"error": "item_id required"}), 400

    history = user_history.setdefault(user_id, {})
    history[item_id] = history.get(item_id, 0) + 1

    recents = user_recents.setdefault(user_id, [])
    recents.insert(0, item_id)
    user_recents[user_id] = recents[:10]

    return jsonify({"status": "logged"})


@app.route("/api/favorites", methods=["GET", "POST"])
def favorites() -> Any:
    user_id = request.args.get("user_id", "default")
    if request.method == "POST":
        payload = request.get_json(force=True)
        item_id = payload.get("item_id")
        if not item_id:
            return jsonify({"error": "item_id required"}), 400
        favorites_set = user_favorites.setdefault(user_id, set())
        favorites_set.add(item_id)
        return jsonify({"status": "added"})

    favorites_set = user_favorites.get(user_id, set())
    items = [item_to_dict(resolve_item(user_id, item_id)) for item_id in favorites_set]
    return jsonify({"favorites": items})


@app.route("/api/recents")
def recents() -> Any:
    user_id = request.args.get("user_id", "default")
    recents_list = user_recents.get(user_id, [])
    items = [item_to_dict(resolve_item(user_id, item_id)) for item_id in recents_list]
    return jsonify({"recents": items})


@app.route("/api/custom_macros", methods=["GET", "POST"])
def custom_macro_handler() -> Any:
    user_id = request.args.get("user_id", "default")
    if request.method == "POST":
        payload = request.get_json(force=True)
        name = payload.get("name")
        protein = int(payload.get("protein", 0))
        carbs = int(payload.get("carbs", 0))
        fat = int(payload.get("fat", 0))
        calories = int(payload.get("calories") or (protein * 4 + carbs * 4 + fat * 9))
        if not name:
            return jsonify({"error": "name required"}), 400
        item = FoodItem(
            id=str(uuid.uuid4()),
            name=name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            popularity=0.35,
            source="custom",
        )
        custom_macros.setdefault(user_id, []).append(item)
        return jsonify({"item": item_to_dict(item)})

    items = [item_to_dict(item) for item in custom_macros.get(user_id, [])]
    return jsonify({"custom_macros": items})


@app.route("/api/meal_templates", methods=["GET", "POST"])
def meal_templates_handler() -> Any:
    user_id = request.args.get("user_id", "default")
    if request.method == "POST":
        payload = request.get_json(force=True)
        name = payload.get("name")
        items = payload.get("items", [])
        if not name or not items:
            return jsonify({"error": "name and items required"}), 400
        resolved_items = [resolve_item(user_id, item_id) for item_id in items]
        template_id = str(uuid.uuid4())
        template = {
            "id": template_id,
            "name": name,
            "items": [item_to_dict(item) for item in resolved_items],
        }
        template["totals"] = calculate_totals(template["items"])
        meal_templates.setdefault(user_id, []).append(template)
        return jsonify({"template": template})

    return jsonify({"templates": meal_templates.get(user_id, [])})


@app.route("/api/cache/stats")
def cache_stats() -> Any:
    frequent_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)
    formatted = [
        {"query": key[1], "user_id": key[0], "hits": count}
        for key, count in frequent_queries
    ]
    return jsonify({"cache_size": len(search_cache), "frequent_queries": formatted[:5]})


def calculate_totals(items: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "calories": sum(item["calories"] for item in items),
        "protein": sum(item["protein"] for item in items),
        "carbs": sum(item["carbs"] for item in items),
        "fat": sum(item["fat"] for item in items),
    }


def resolve_item(user_id: str, item_id: str) -> FoodItem:
    for item in custom_macros.get(user_id, []):
        if item.id == item_id:
            return item
    for item in FOODS:
        if item.id == item_id:
            return item
    return FoodItem(item_id, "Unknown Item", 0, 0, 0, 0, 0.0)


def item_to_dict(item: FoodItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "calories": item.calories,
        "protein": item.protein,
        "carbs": item.carbs,
        "fat": item.fat,
        "popularity": item.popularity,
        "source": item.source,
    }


def text_match_score(name: str, query: str) -> float:
    name_lower = name.lower()
    query_lower = query.lower()
    if query_lower in name_lower:
        return min(1.0, len(query_lower) / len(name_lower) + 0.6)
    name_tokens = set(name_lower.split())
    query_tokens = set(query_lower.split())
    overlap = name_tokens & query_tokens
    if not overlap:
        return 0
    return min(1.0, len(overlap) / len(name_tokens))


def get_cached_results(cache_key: tuple[str, str]) -> list[dict[str, Any]] | None:
    cached = search_cache.get(cache_key)
    if not cached:
        return None
    if time.time() - cached["timestamp"] > CACHE_TTL and cached["hits"] < 3:
        search_cache.pop(cache_key, None)
        return None
    cached["timestamp"] = time.time()
    cached["hits"] += 1
    return cached["results"]


def store_cached_results(cache_key: tuple[str, str], results: list[dict[str, Any]]) -> None:
    query_counts[cache_key] = query_counts.get(cache_key, 0) + 1
    search_cache[cache_key] = {
        "timestamp": time.time(),
        "results": results,
        "hits": 1,
    }
    if len(search_cache) > CACHE_MAX:
        oldest_key = min(search_cache.items(), key=lambda item: item[1]["timestamp"])[0]
        search_cache.pop(oldest_key, None)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
