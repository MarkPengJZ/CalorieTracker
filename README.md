# CalorieTracker

Minimal photo logging flow that uses an **on-device model** placeholder (deterministic hashing) to propose candidate foods. Users must confirm the label and portion size, and confirmed entries are persisted to a feedback dataset for future improvements.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000 to use the logging UI.

## API

- `POST /photo-log` (multipart form with `photo`)
  - Returns candidate foods + confidences and a `log_id`.
  - Marks the entry as `pending_confirmation`.
- `POST /photo-log/confirm`
  - JSON body: `log_id`, `confirmed_label`, `portion_grams`.
  - Persists confirmation to `data/feedback.jsonl` for future model training.

## Data files

- `data/photo_logs.jsonl` stores raw photo log metadata and confirmations.
- `data/feedback.jsonl` stores confirmed labels + portions for model improvement.
## Product Documentation
- [Product Spec](docs/product-spec.md)
