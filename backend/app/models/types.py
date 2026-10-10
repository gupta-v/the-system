"""Reusable validated field types. Use these instead of bare `int`/`str`/`float` in models."""

from datetime import date
from typing import Annotated
from uuid import UUID
from zoneinfo import available_timezones

from pydantic import AfterValidator, Field, StringConstraints

# Text
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
GoalName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
DayTypeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
Unit = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=16)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]

# Numbers
Id = UUID
Weekday = Annotated[int, Field(ge=0, le=6, description="0 = Monday .. 6 = Sunday")]
ResetHour = Annotated[int, Field(ge=0, le=23, description="Local hour the game day resets")]
Target = Annotated[float, Field(gt=0, le=1_000_000)]
Progress = Annotated[float, Field(ge=0, le=1_000_000)]
Weight = Annotated[float, Field(gt=0, le=10, description="Share of the day's 100 base XP")]
Sets = Annotated[int, Field(ge=2, le=20, description="Split the Goal into this many taps")]
Fraction = Annotated[float, Field(ge=0, le=1)]
HeightCm = Annotated[float, Field(ge=50, le=272, description="Height in cm")]
WeightKg = Annotated[float, Field(ge=20, le=500, description="Weight in kg")]


def _check_timezone(tz: str) -> str:
    if tz not in available_timezones():
        raise ValueError(f"unknown timezone: {tz}")
    return tz


Timezone = Annotated[str, AfterValidator(_check_timezone)]


def _check_birth_date(born: date) -> date:
    years = age(born, date.today())
    if not 5 <= years <= 120:
        raise ValueError("age must be between 5 and 120")
    return born


def age(born: date, today: date) -> int:
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


BirthDate = Annotated[date, AfterValidator(_check_birth_date)]
