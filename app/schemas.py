from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    name: str
    email: EmailStr
    timezone: str = "UTC"


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    timezone: Optional[str] = None


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class GoalConfigBase(BaseModel):
    calories_target: Optional[int] = None
    protein_target: Optional[float] = None
    carbs_target: Optional[float] = None
    fat_target: Optional[float] = None
    weight_target: Optional[float] = None


class GoalConfigCreate(GoalConfigBase):
    pass


class GoalConfigOut(GoalConfigBase):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        orm_mode = True


class DailyLogBase(BaseModel):
    log_date: date
    timezone: str = "UTC"


class DailyLogCreate(DailyLogBase):
    pass


class DailyLogOut(DailyLogBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class MealBase(BaseModel):
    name: str
    eaten_at: Optional[datetime] = None
    note: Optional[str] = None


class MealCreate(MealBase):
    pass


class MealOut(MealBase):
    id: int
    daily_log_id: int

    class Config:
        orm_mode = True


class FoodItemBase(BaseModel):
    name: str
    calories: int
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    quantity: float = Field(default=1, ge=0)


class FoodItemCreate(FoodItemBase):
    pass


class FoodItemOut(FoodItemBase):
    id: int
    meal_id: int

    class Config:
        orm_mode = True


class MacroTotalsOut(BaseModel):
    id: int
    daily_log_id: int
    calories_total: int
    protein_total: float
    carbs_total: float
    fat_total: float
    updated_at: datetime

    class Config:
        orm_mode = True


class WeightEntryBase(BaseModel):
    entry_date: date
    weight: float
    note: Optional[str] = None


class WeightEntryCreate(WeightEntryBase):
    pass


class WeightEntryOut(WeightEntryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class DailySummary(BaseModel):
    log_date: date
    calories_total: int
    protein_total: float
    carbs_total: float
    fat_total: float


class WeeklySummary(BaseModel):
    week_start: date
    week_end: date
    calories_total: int
    protein_total: float
    carbs_total: float
    fat_total: float


class SummaryResponse(BaseModel):
    daily: List[DailySummary]
    weekly: List[WeeklySummary]
