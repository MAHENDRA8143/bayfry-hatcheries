"""FastAPI entrypoint for deployment.

This service intentionally stays lightweight on startup so Render can keep the
container alive and expose HTTP endpoints without running the simulation loop.
"""

import math
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import PROJECT_NAME, PROJECT_VERSION, SAFE_RANGES
from data_generator import WaterQualityDataGenerator


app = FastAPI(title=PROJECT_NAME, version=PROJECT_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

demo_users = {
    "operator": "operator123",
    "admin": "admin123",
}


class LoginRequest(BaseModel):
    username: str
    password: str


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _serialize_record(record: dict[str, Any], source: str = "Plant SCADA") -> dict[str, Any]:
    timestamp = record["Timestamp"]
    cycle = timestamp.timestamp() / 18000
    anomaly = record.get("Anomaly") or ""
    return {
        "timestamp": timestamp.isoformat(),
        "source": "Generated anomaly" if anomaly else source,
        "salinity": record["Salinity"],
        "temperature": record["Temperature"],
        "do": record["DO"],
        "ph": record["pH"],
        "alkalinity": record["Alkalinity"],
        "anomaly": anomaly,
        "bod": _round(22 + math.sin(cycle) * 4 + (14 if anomaly else 0), 1),
        "cod": _round(178 + math.cos(cycle / 1.4) * 22 + (92 if anomaly else 0), 1),
        "nh3n": _round(6 + math.sin(cycle / 1.6) * 1.4 + (3.5 if anomaly else 0), 2),
        "tp": _round(2.3 + math.cos(cycle / 2.1) * 0.45 + (1.1 if anomaly else 0), 2),
    }


def _current_records(hours: int) -> list[dict[str, Any]]:
    bounded_hours = max(1, min(hours, 720))
    generator = WaterQualityDataGenerator(seed=42)
    data = generator.generate_historical_data(num_hours=bounded_hours)
    return [_serialize_record(row, "Plant SCADA") for row in data.to_dict("records")]


def _forecast_day(day_offset: int, base: dict[str, Any]) -> dict[str, Any]:
    date = datetime.now() + timedelta(days=day_offset)
    hours = []
    for hour in range(24):
        cycle = (hour + day_offset * 5) / 4
        surge = day_offset == 3 and 9 < hour < 16
        timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
        anomaly = "FORECAST_SURGE" if surge and hour % 3 == 0 else ""
        hours.append({
            "timestamp": timestamp.isoformat(),
            "source": "Forecast model",
            "salinity": _round(base["salinity"] + math.sin(cycle / 2.2) * 0.26 - (1.6 if surge else 0), 2),
            "temperature": _round(base["temperature"] + math.cos(cycle / 2.5) * 1.2 + (1.8 if surge else 0), 2),
            "do": _round(base["do"] + math.cos(cycle) * 0.55 - day_offset * 0.08 - (1.8 if surge else 0), 2),
            "ph": _round(7.35 + math.sin(cycle / 1.6) * 0.35 + (0.6 if surge else 0), 2),
            "alkalinity": _round(base["alkalinity"] + math.sin(cycle / 2.7) * 5 - (18 if surge else 0), 2),
            "anomaly": anomaly,
        })
    return {
        "date": date.date().isoformat(),
        "summary": "Model forecast",
        "hours": hours,
    }


@app.get("/")
def root():
    return {
        "message": "API running",
        "project": PROJECT_NAME,
        "version": PROJECT_VERSION,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    return {
        "project": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "safe_ranges": SAFE_RANGES,
    }


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    if demo_users.get(payload.username) != payload.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "access_token": f"demo-{payload.username}-{int(datetime.now().timestamp())}",
        "token_type": "bearer",
    }


@app.get("/api/data/current")
def current_data(hours: int = 96):
    return {"records": _current_records(hours)}


@app.get("/api/predictions/next-day")
def next_day_predictions(history_hours: int = 72):
    records = _current_records(history_hours)
    base = records[-1]
    return {
        "forecast": [_forecast_day(day_offset, base) for day_offset in range(1, 8)]
    }
