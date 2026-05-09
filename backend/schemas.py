from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


DailyStatus = Literal["GREEN", "YELLOW", "RED", "INCOMPLETE"]
RecommendationAction = Literal[
    "KEEP",
    "REDUCE",
    "RECOVERY",
    "REST",
    "INDOOR_ALTERNATIVE",
    "NO_TRAINING_TODAY",
    "SYNC_REQUIRED",
]


class PlannedWorkout(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    planned_tss: Optional[float] = None
    source: Optional[str] = None  # FasCat, Intervals, manual, etc.


class CompletedActivity(BaseModel):
    exists: bool = False
    name: Optional[str] = None
    duration_minutes: Optional[int] = None
    tss: Optional[float] = None
    avg_power: Optional[float] = None
    normalized_power: Optional[float] = None
    intensity_factor: Optional[float] = None


class ReadinessData(BaseModel):
    sleep_available: bool = False
    hrv_available: bool = False
    resting_hr_available: bool = False

    sleep_hours: Optional[float] = None
    hrv: Optional[float] = None
    resting_hr: Optional[float] = None

    fitness_ctl: Optional[float] = None
    fatigue_atl: Optional[float] = None
    form: Optional[float] = None

    notes: Optional[str] = None


class WeightData(BaseModel):
    current_kg: Optional[float] = None
    avg_7d_kg: Optional[float] = None
    target_kg: float = 74.0
    weekly_trend_kg: Optional[float] = None
    guidance: Optional[str] = None


class FuelingAdvice(BaseModel):
    protein_target_g: str = "150–170 g/dia"
    carb_guidance: Optional[str] = None
    deficit_guidance: Optional[str] = None
    notes: Optional[str] = None


class ReportFlags(BaseModel):
    incomplete_essential_data: bool = False
    already_trained_today: bool = False
    missed_yesterday_workout: bool = False
    weekend_indoor_option_available: bool = False

    no_bike_week: bool = False
    sick: bool = False
    injured: bool = False
    race_week: bool = False

    rain_or_indoor_constraint: bool = False
    no_time_constraint: bool = False


class Recommendation(BaseModel):
    action: RecommendationAction
    headline: str
    details: str
    workout_modification: Optional[str] = None
    indoor_alternative: Optional[str] = None


class DailyCoachReport(BaseModel):
    date: date
    generated_at: datetime

    status: DailyStatus
    title: str
    summary: str
    full_text: str

    planned_workout: PlannedWorkout = Field(default_factory=PlannedWorkout)
    completed_activity: CompletedActivity = Field(default_factory=CompletedActivity)
    readiness: ReadinessData = Field(default_factory=ReadinessData)
    weight: WeightData = Field(default_factory=WeightData)
    fueling: FuelingAdvice = Field(default_factory=FuelingAdvice)
    recommendation: Recommendation
    flags: ReportFlags = Field(default_factory=ReportFlags)

    source_plan: str = "FasCat"
    auto_apply: bool = False
