import hashlib
from dataclasses import dataclass
from typing import List

FOOD_CANDIDATES = [
    "grilled chicken",
    "caesar salad",
    "avocado toast",
    "spaghetti bolognese",
    "veggie stir fry",
    "greek yogurt",
    "berry smoothie",
    "sushi roll",
    "beef burrito",
    "miso soup",
]


@dataclass(frozen=True)
class Candidate:
    label: str
    confidence: float


def _ranked_candidates(seed: bytes) -> List[Candidate]:
    digest = hashlib.sha256(seed).hexdigest()
    start = int(digest[:4], 16) % len(FOOD_CANDIDATES)
    ordered = FOOD_CANDIDATES[start:] + FOOD_CANDIDATES[:start]
    confidences = [0.72, 0.61, 0.49]
    return [Candidate(label=label, confidence=confidences[idx]) for idx, label in enumerate(ordered[:3])]


def run_on_device_inference(filename: str, payload: bytes) -> List[Candidate]:
    """Simulated on-device model that hashes the image content for deterministic candidates."""
    seed = f"{filename}:{len(payload)}".encode("utf-8") + payload[:64]
    return _ranked_candidates(seed)
