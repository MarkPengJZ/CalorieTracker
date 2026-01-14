from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    daily_logs = relationship("DailyLog", back_populates="user", cascade="all, delete-orphan")
    weight_entries = relationship("WeightEntry", back_populates="user", cascade="all, delete-orphan")
    goal_config = relationship("GoalConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")


class GoalConfig(Base):
    __tablename__ = "goal_configs"
    __table_args__ = (UniqueConstraint("user_id", name="uq_goal_config_user"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    calories_target = Column(Integer, nullable=True)
    protein_target = Column(Float, nullable=True)
    carbs_target = Column(Float, nullable=True)
    fat_target = Column(Float, nullable=True)
    weight_target = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="goal_config")


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_daily_log_user_date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(Date, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="daily_logs")
    meals = relationship("Meal", back_populates="daily_log", cascade="all, delete-orphan")
    macro_totals = relationship(
        "MacroTotals",
        back_populates="daily_log",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    daily_log_id = Column(Integer, ForeignKey("daily_logs.id"), nullable=False)
    name = Column(String, nullable=False)
    eaten_at = Column(DateTime(timezone=True), nullable=True)
    note = Column(String, nullable=True)

    daily_log = relationship("DailyLog", back_populates="meals")
    food_items = relationship("FoodItem", back_populates="meal", cascade="all, delete-orphan")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    name = Column(String, nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False, default=0)
    carbs = Column(Float, nullable=False, default=0)
    fat = Column(Float, nullable=False, default=0)
    quantity = Column(Float, nullable=False, default=1)

    meal = relationship("Meal", back_populates="food_items")


class MacroTotals(Base):
    __tablename__ = "macro_totals"
    __table_args__ = (UniqueConstraint("daily_log_id", name="uq_macro_totals_daily_log"),)

    id = Column(Integer, primary_key=True, index=True)
    daily_log_id = Column(Integer, ForeignKey("daily_logs.id"), nullable=False)
    calories_total = Column(Integer, nullable=False, default=0)
    protein_total = Column(Float, nullable=False, default=0)
    carbs_total = Column(Float, nullable=False, default=0)
    fat_total = Column(Float, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    daily_log = relationship("DailyLog", back_populates="macro_totals")


class WeightEntry(Base):
    __tablename__ = "weight_entries"
    __table_args__ = (UniqueConstraint("user_id", "entry_date", name="uq_weight_entry_user_date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    weight = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="weight_entries")
