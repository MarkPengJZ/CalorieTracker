from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from . import models


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def list_users(db: Session) -> List[models.User]:
    return db.query(models.User).all()


def create_user(db: Session, name: str, email: str, timezone: str) -> models.User:
    user = models.User(name=name, email=email, timezone=timezone)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: models.User, updates: Dict) -> models.User:
    for key, value in updates.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: models.User) -> None:
    db.delete(user)
    db.commit()


def get_goal_config(db: Session, user_id: int) -> Optional[models.GoalConfig]:
    return db.query(models.GoalConfig).filter(models.GoalConfig.user_id == user_id).first()


def upsert_goal_config(db: Session, user_id: int, updates: Dict) -> models.GoalConfig:
    goal = get_goal_config(db, user_id)
    if goal:
        for key, value in updates.items():
            setattr(goal, key, value)
    else:
        goal = models.GoalConfig(user_id=user_id, **updates)
        db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal_config(db: Session, goal: models.GoalConfig) -> None:
    db.delete(goal)
    db.commit()


def get_daily_log(db: Session, user_id: int, log_date: date) -> Optional[models.DailyLog]:
    return (
        db.query(models.DailyLog)
        .filter(models.DailyLog.user_id == user_id, models.DailyLog.log_date == log_date)
        .first()
    )


def list_daily_logs(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[models.DailyLog]:
    query = db.query(models.DailyLog).filter(models.DailyLog.user_id == user_id)
    if start_date:
        query = query.filter(models.DailyLog.log_date >= start_date)
    if end_date:
        query = query.filter(models.DailyLog.log_date <= end_date)
    return query.order_by(models.DailyLog.log_date).all()


def upsert_daily_log(
    db: Session,
    user: models.User,
    log_date: date,
    timezone: str,
) -> models.DailyLog:
    existing = get_daily_log(db, user.id, log_date)
    if existing:
        existing.timezone = timezone
        db.commit()
        db.refresh(existing)
        return existing
    daily_log = models.DailyLog(user_id=user.id, log_date=log_date, timezone=timezone)
    db.add(daily_log)
    db.commit()
    db.refresh(daily_log)
    ensure_macro_totals(db, daily_log)
    return daily_log


def delete_daily_log(db: Session, daily_log: models.DailyLog) -> None:
    db.delete(daily_log)
    db.commit()


def create_meal(db: Session, daily_log: models.DailyLog, data: Dict) -> models.Meal:
    meal = models.Meal(daily_log_id=daily_log.id, **data)
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def get_meal(db: Session, meal_id: int) -> Optional[models.Meal]:
    return db.query(models.Meal).filter(models.Meal.id == meal_id).first()


def list_meals(db: Session, daily_log_id: int) -> List[models.Meal]:
    return db.query(models.Meal).filter(models.Meal.daily_log_id == daily_log_id).all()


def update_meal(db: Session, meal: models.Meal, updates: Dict) -> models.Meal:
    for key, value in updates.items():
        setattr(meal, key, value)
    db.commit()
    db.refresh(meal)
    return meal


def delete_meal(db: Session, meal: models.Meal) -> None:
    daily_log_id = meal.daily_log_id
    db.delete(meal)
    db.commit()
    refresh_macro_totals_for_log(db, daily_log_id)


def create_food_item(db: Session, meal: models.Meal, data: Dict) -> models.FoodItem:
    item = models.FoodItem(meal_id=meal.id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    refresh_macro_totals_for_log(db, meal.daily_log_id)
    return item


def get_food_item(db: Session, item_id: int) -> Optional[models.FoodItem]:
    return db.query(models.FoodItem).filter(models.FoodItem.id == item_id).first()


def list_food_items(db: Session, meal_id: int) -> List[models.FoodItem]:
    return db.query(models.FoodItem).filter(models.FoodItem.meal_id == meal_id).all()


def update_food_item(db: Session, item: models.FoodItem, updates: Dict) -> models.FoodItem:
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    refresh_macro_totals_for_log(db, item.meal.daily_log_id)
    return item


def delete_food_item(db: Session, item: models.FoodItem) -> None:
    daily_log_id = item.meal.daily_log_id
    db.delete(item)
    db.commit()
    refresh_macro_totals_for_log(db, daily_log_id)


def get_weight_entry(db: Session, entry_id: int) -> Optional[models.WeightEntry]:
    return db.query(models.WeightEntry).filter(models.WeightEntry.id == entry_id).first()


def list_weight_entries(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[models.WeightEntry]:
    query = db.query(models.WeightEntry).filter(models.WeightEntry.user_id == user_id)
    if start_date:
        query = query.filter(models.WeightEntry.entry_date >= start_date)
    if end_date:
        query = query.filter(models.WeightEntry.entry_date <= end_date)
    return query.order_by(models.WeightEntry.entry_date).all()


def upsert_weight_entry(db: Session, user_id: int, entry_date: date, updates: Dict) -> models.WeightEntry:
    existing = (
        db.query(models.WeightEntry)
        .filter(models.WeightEntry.user_id == user_id, models.WeightEntry.entry_date == entry_date)
        .first()
    )
    if existing:
        for key, value in updates.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    entry = models.WeightEntry(user_id=user_id, entry_date=entry_date, **updates)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_weight_entry(db: Session, entry: models.WeightEntry, updates: Dict) -> models.WeightEntry:
    for key, value in updates.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_weight_entry(db: Session, entry: models.WeightEntry) -> None:
    db.delete(entry)
    db.commit()


def ensure_macro_totals(db: Session, daily_log: models.DailyLog) -> models.MacroTotals:
    totals = (
        db.query(models.MacroTotals)
        .filter(models.MacroTotals.daily_log_id == daily_log.id)
        .first()
    )
    if totals:
        return totals
    totals = models.MacroTotals(daily_log_id=daily_log.id)
    db.add(totals)
    db.commit()
    db.refresh(totals)
    return totals


def refresh_macro_totals_for_log(db: Session, daily_log_id: int) -> models.MacroTotals:
    totals = (
        db.query(
            func.coalesce(func.sum(models.FoodItem.calories * models.FoodItem.quantity), 0),
            func.coalesce(func.sum(models.FoodItem.protein * models.FoodItem.quantity), 0.0),
            func.coalesce(func.sum(models.FoodItem.carbs * models.FoodItem.quantity), 0.0),
            func.coalesce(func.sum(models.FoodItem.fat * models.FoodItem.quantity), 0.0),
        )
        .join(models.Meal, models.Meal.id == models.FoodItem.meal_id)
        .filter(models.Meal.daily_log_id == daily_log_id)
        .first()
    )
    totals_row = (
        db.query(models.MacroTotals)
        .filter(models.MacroTotals.daily_log_id == daily_log_id)
        .first()
    )
    if not totals_row:
        totals_row = models.MacroTotals(daily_log_id=daily_log_id)
        db.add(totals_row)
    totals_row.calories_total = int(totals[0] or 0)
    totals_row.protein_total = float(totals[1] or 0)
    totals_row.carbs_total = float(totals[2] or 0)
    totals_row.fat_total = float(totals[3] or 0)
    db.commit()
    db.refresh(totals_row)
    return totals_row


def build_daily_summaries(
    db: Session,
    user: models.User,
    start_date: date,
    end_date: date,
) -> List[Tuple[date, int, float, float, float]]:
    logs = list_daily_logs(db, user.id, start_date, end_date)
    summaries: List[Tuple[date, int, float, float, float]] = []
    for log in logs:
        totals = refresh_macro_totals_for_log(db, log.id)
        summaries.append(
            (
                log.log_date,
                totals.calories_total,
                totals.protein_total,
                totals.carbs_total,
                totals.fat_total,
            )
        )
    return summaries


def build_weekly_summaries(
    daily_summaries: List[Tuple[date, int, float, float, float]],
    timezone: str,
) -> List[Tuple[date, date, int, float, float, float]]:
    if not daily_summaries:
        return []
    ZoneInfo(timezone)
    buckets: Dict[date, List[Tuple[int, float, float, float]]] = defaultdict(list)
    for log_date, calories, protein, carbs, fat in daily_summaries:
        week_start = log_date - timedelta(days=log_date.weekday())
        buckets[week_start].append((calories, protein, carbs, fat))
    results = []
    for week_start, entries in sorted(buckets.items()):
        calories_total = sum(item[0] for item in entries)
        protein_total = sum(item[1] for item in entries)
        carbs_total = sum(item[2] for item in entries)
        fat_total = sum(item[3] for item in entries)
        week_end = week_start + timedelta(days=6)
        results.append(
            (week_start, week_end, calories_total, protein_total, carbs_total, fat_total)
        )
    return results


def resolve_timezone(requested: Optional[str], fallback: str) -> str:
    candidate = requested or fallback
    ZoneInfo(candidate)
    return candidate
