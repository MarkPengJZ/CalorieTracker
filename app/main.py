from datetime import date
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CalorieTracker API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    timezone = crud.resolve_timezone(user.timezone, "UTC")
    return crud.create_user(db, user.name, user.email, timezone)


@app.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return crud.list_users(db)


@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, update: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updates = update.dict(exclude_unset=True)
    if "timezone" in updates:
        updates["timezone"] = crud.resolve_timezone(updates["timezone"], user.timezone)
    return crud.update_user(db, user, updates)


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, user)
    return {"status": "deleted"}


@app.get("/users/{user_id}/goals", response_model=schemas.GoalConfigOut)
def get_goals(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    goal = crud.get_goal_config(db, user_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal config not found")
    return goal


@app.put("/users/{user_id}/goals", response_model=schemas.GoalConfigOut)
def upsert_goals(user_id: int, payload: schemas.GoalConfigCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    goal = crud.upsert_goal_config(db, user_id, payload.dict(exclude_unset=True))
    return goal


@app.delete("/users/{user_id}/goals")
def delete_goals(user_id: int, db: Session = Depends(get_db)):
    goal = crud.get_goal_config(db, user_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal config not found")
    crud.delete_goal_config(db, goal)
    return {"status": "deleted"}


@app.get("/users/{user_id}/daily-logs", response_model=List[schemas.DailyLogOut])
def list_daily_logs(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.list_daily_logs(db, user_id, start_date, end_date)


@app.post("/users/{user_id}/daily-logs", response_model=schemas.DailyLogOut)
def create_daily_log(user_id: int, payload: schemas.DailyLogCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    timezone = crud.resolve_timezone(payload.timezone, user.timezone)
    log = crud.upsert_daily_log(db, user, payload.log_date, timezone)
    return log


@app.get("/users/{user_id}/daily-logs/{log_date}", response_model=schemas.DailyLogOut)
def get_daily_log(user_id: int, log_date: date, db: Session = Depends(get_db)):
    log = crud.get_daily_log(db, user_id, log_date)
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    return log


@app.put("/users/{user_id}/daily-logs/{log_date}", response_model=schemas.DailyLogOut)
def upsert_daily_log(user_id: int, log_date: date, payload: schemas.DailyLogCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    timezone = crud.resolve_timezone(payload.timezone, user.timezone)
    log = crud.upsert_daily_log(db, user, log_date, timezone)
    return log


@app.delete("/users/{user_id}/daily-logs/{log_date}")
def delete_daily_log(user_id: int, log_date: date, db: Session = Depends(get_db)):
    log = crud.get_daily_log(db, user_id, log_date)
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    crud.delete_daily_log(db, log)
    return {"status": "deleted"}


@app.get("/daily-logs/{daily_log_id}/meals", response_model=List[schemas.MealOut])
def list_meals(daily_log_id: int, db: Session = Depends(get_db)):
    return crud.list_meals(db, daily_log_id)


@app.post("/daily-logs/{daily_log_id}/meals", response_model=schemas.MealOut)
def create_meal(daily_log_id: int, payload: schemas.MealCreate, db: Session = Depends(get_db)):
    daily_log = db.query(models.DailyLog).filter(models.DailyLog.id == daily_log_id).first()
    if not daily_log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    meal = crud.create_meal(db, daily_log, payload.dict(exclude_unset=True))
    return meal


@app.get("/meals/{meal_id}", response_model=schemas.MealOut)
def get_meal(meal_id: int, db: Session = Depends(get_db)):
    meal = crud.get_meal(db, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


@app.put("/meals/{meal_id}", response_model=schemas.MealOut)
def update_meal(meal_id: int, payload: schemas.MealCreate, db: Session = Depends(get_db)):
    meal = crud.get_meal(db, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return crud.update_meal(db, meal, payload.dict(exclude_unset=True))


@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    meal = crud.get_meal(db, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    crud.delete_meal(db, meal)
    return {"status": "deleted"}


@app.get("/meals/{meal_id}/food-items", response_model=List[schemas.FoodItemOut])
def list_food_items(meal_id: int, db: Session = Depends(get_db)):
    return crud.list_food_items(db, meal_id)


@app.post("/meals/{meal_id}/food-items", response_model=schemas.FoodItemOut)
def create_food_item(meal_id: int, payload: schemas.FoodItemCreate, db: Session = Depends(get_db)):
    meal = crud.get_meal(db, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    item = crud.create_food_item(db, meal, payload.dict(exclude_unset=True))
    return item


@app.get("/food-items/{item_id}", response_model=schemas.FoodItemOut)
def get_food_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_food_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Food item not found")
    return item


@app.put("/food-items/{item_id}", response_model=schemas.FoodItemOut)
def update_food_item(item_id: int, payload: schemas.FoodItemCreate, db: Session = Depends(get_db)):
    item = crud.get_food_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Food item not found")
    return crud.update_food_item(db, item, payload.dict(exclude_unset=True))


@app.delete("/food-items/{item_id}")
def delete_food_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_food_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Food item not found")
    crud.delete_food_item(db, item)
    return {"status": "deleted"}


@app.get("/daily-logs/{daily_log_id}/macro-totals", response_model=schemas.MacroTotalsOut)
def get_macro_totals(daily_log_id: int, db: Session = Depends(get_db)):
    totals = (
        db.query(models.MacroTotals)
        .filter(models.MacroTotals.daily_log_id == daily_log_id)
        .first()
    )
    if not totals:
        totals = crud.refresh_macro_totals_for_log(db, daily_log_id)
    return totals


@app.get("/users/{user_id}/weight-entries", response_model=List[schemas.WeightEntryOut])
def list_weight_entries(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.list_weight_entries(db, user_id, start_date, end_date)


@app.post("/users/{user_id}/weight-entries", response_model=schemas.WeightEntryOut)
def create_weight_entry(user_id: int, payload: schemas.WeightEntryCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    entry = crud.upsert_weight_entry(
        db,
        user_id,
        payload.entry_date,
        {"weight": payload.weight, "note": payload.note},
    )
    return entry


@app.get("/weight-entries/{entry_id}", response_model=schemas.WeightEntryOut)
def get_weight_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = crud.get_weight_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Weight entry not found")
    return entry


@app.put("/weight-entries/{entry_id}", response_model=schemas.WeightEntryOut)
def update_weight_entry(entry_id: int, payload: schemas.WeightEntryCreate, db: Session = Depends(get_db)):
    entry = crud.get_weight_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Weight entry not found")
    updates = {"entry_date": payload.entry_date, "weight": payload.weight, "note": payload.note}
    return crud.update_weight_entry(db, entry, updates)


@app.delete("/weight-entries/{entry_id}")
def delete_weight_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = crud.get_weight_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Weight entry not found")
    crud.delete_weight_entry(db, entry)
    return {"status": "deleted"}


@app.get("/users/{user_id}/summaries", response_model=schemas.SummaryResponse)
def get_summaries(
    user_id: int,
    start_date: date,
    end_date: date,
    timezone: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tz = crud.resolve_timezone(timezone, user.timezone)
    daily = crud.build_daily_summaries(db, user, start_date, end_date)
    weekly = crud.build_weekly_summaries(daily, tz)
    daily_payload = [
        schemas.DailySummary(
            log_date=item[0],
            calories_total=item[1],
            protein_total=item[2],
            carbs_total=item[3],
            fat_total=item[4],
        )
        for item in daily
    ]
    weekly_payload = [
        schemas.WeeklySummary(
            week_start=item[0],
            week_end=item[1],
            calories_total=item[2],
            protein_total=item[3],
            carbs_total=item[4],
            fat_total=item[5],
        )
        for item in weekly
    ]
    return schemas.SummaryResponse(daily=daily_payload, weekly=weekly_payload)
