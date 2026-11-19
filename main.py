from datetime import date, timedelta
import hashlib
import random

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="Synthetic Weather API",
    description="REST API с синтетическими данными о погоде.",
    version="1.0.0",
)


class WeatherResponse(BaseModel):
    city: str
    date: date
    temperature_c: float
    feels_like_c: float
    humidity_percent: int = Field(ge=0, le=100)
    wind_speed_kmh: float = Field(ge=0)
    condition: str


class ForecastResponse(BaseModel):
    city: str
    forecast: list[WeatherResponse]


CONDITIONS = [
    "sunny",
    "partly_cloudy",
    "cloudy",
    "rain",
    "snow",
    "windy",
]


def make_weather(city: str, day: date) -> WeatherResponse:
    """Генерирует стабильные синтетические данные для города и даты."""
    seed_text = f"{city.strip().casefold()}:{day.isoformat()}"
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16)
    rng = random.Random(seed)

    temperature = round(rng.uniform(-10.0, 35.0), 1)
    feels_like = round(temperature + rng.uniform(-4.0, 2.0), 1)

    return WeatherResponse(
        city=city.strip(),
        date=day,
        temperature_c=temperature,
        feels_like_c=feels_like,
        humidity_percent=rng.randint(25, 95),
        wind_speed_kmh=round(rng.uniform(0.0, 40.0), 1),
        condition=rng.choice(CONDITIONS),
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/weather", response_model=WeatherResponse)
def get_weather(
    city: str = Query(..., min_length=1, max_length=100),
    day: date | None = Query(default=None, description="Дата в формате YYYY-MM-DD"),
):
    requested_day = day or date.today()
    return make_weather(city, requested_day)


@app.get("/api/v1/forecast", response_model=ForecastResponse)
def get_forecast(
    city: str = Query(..., min_length=1, max_length=100),
    days: int = Query(default=5, ge=1, le=14),
    start_date: date | None = Query(default=None),
):
    city = city.strip()
    if not city:
        raise HTTPException(status_code=422, detail="Параметр city не должен быть пустым")

    first_day = start_date or date.today()
    forecast = [
        make_weather(city, first_day + timedelta(days=offset))
        for offset in range(days)
    ]

    return ForecastResponse(city=city, forecast=forecast)
