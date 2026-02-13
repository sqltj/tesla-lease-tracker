from datetime import datetime
from typing import Annotated

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User as UserOut
from fastapi import APIRouter, Depends

from .._metadata import api_prefix
from fastapi import HTTPException

from .dependencies import DataStoreDep, RuntimeDep, get_obo_ws
from .forecast import forecast_linear, forecast_timeseries
from .models import (
    DashboardOut,
    ForecastOut,
    HealthOut,
    LeaseConfig,
    LeaseConfigIn,
    LeaseConfigOut,
    MileageReading,
    MileageReadingOut,
    VersionOut,
)
from .tesla_service import TeslaService, TeslaServiceError

api = APIRouter(prefix=api_prefix)


@api.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@api.get("/health", response_model=HealthOut, operation_id="getHealth")
async def health(store: DataStoreDep):
    config = store.data.lease_config
    return HealthOut(
        status="ok",
        version=VersionOut.from_metadata().version,
        has_lease=config is not None,
        readings_count=len(store.data.readings),
        last_sync=store.data.last_sync,
    )


@api.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me(obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)]):
    return obo_ws.current_user.me()


# --- Lease Config ---


@api.get("/lease", response_model=LeaseConfigOut | None, operation_id="getLease")
async def get_lease(store: DataStoreDep):
    return store.data.lease_config


@api.put("/lease", response_model=LeaseConfigOut, operation_id="saveLease")
async def save_lease(lease_in: LeaseConfigIn, store: DataStoreDep):
    now = datetime.utcnow()
    if store.data.lease_config:
        lease = store.data.lease_config.model_copy(
            update={**lease_in.model_dump(), "updated_at": now}
        )
    else:
        lease = LeaseConfig(**lease_in.model_dump(), created_at=now, updated_at=now)
    store.data.lease_config = lease
    store.save()
    return lease


# --- Mileage ---


@api.get("/mileage", response_model=list[MileageReadingOut], operation_id="getMileage")
async def get_mileage(store: DataStoreDep):
    config = store.data.lease_config
    if not config:
        return []
    return [
        MileageReadingOut(
            timestamp=r.timestamp,
            odometer=r.odometer,
            lease_miles=r.odometer - config.start_odometer,
        )
        for r in store.data.readings
    ]


@api.post("/mileage/sync", response_model=MileageReadingOut, operation_id="syncMileage")
async def sync_mileage(store: DataStoreDep, runtime: RuntimeDep):
    config = store.data.lease_config
    if not config:
        raise HTTPException(status_code=400, detail="No lease configured")

    try:
        service = TeslaService(runtime)
        odometer = await service.fetch_odometer(config.vin)
    except TeslaServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    now = datetime.utcnow()
    reading = MileageReading(timestamp=now, odometer=odometer)
    store.data.readings.append(reading)
    store.data.last_sync = now
    store.save()

    return MileageReadingOut(
        timestamp=now,
        odometer=odometer,
        lease_miles=odometer - config.start_odometer,
    )


# --- Dashboard ---


@api.get("/dashboard", response_model=DashboardOut | None, operation_id="getDashboard")
async def get_dashboard(store: DataStoreDep):
    config = store.data.lease_config
    if not config:
        return None

    readings = store.data.readings
    start_odo = config.start_odometer
    today = datetime.utcnow().date()
    lease_start = config.lease_start_date
    lease_end = config.lease_end_date

    total_days = (lease_end - lease_start).days
    days_elapsed = max((today - lease_start).days, 1)
    days_remaining = max((lease_end - today).days, 0)

    if readings:
        last = readings[-1]
        lease_miles_used = last.odometer - start_odo
        last_odometer = last.odometer
    else:
        lease_miles_used = 0
        last_odometer = None

    daily_average = lease_miles_used / days_elapsed if days_elapsed > 0 else 0
    budget_daily_rate = config.mileage_limit / total_days if total_days > 0 else 0
    projected_end = daily_average * total_days
    over_under = projected_end - config.mileage_limit

    return DashboardOut(
        lease_miles_used=lease_miles_used,
        mileage_limit=config.mileage_limit,
        daily_average=round(daily_average, 1),
        budget_daily_rate=round(budget_daily_rate, 1),
        days_remaining=days_remaining,
        total_lease_days=total_days,
        projected_end_miles=round(projected_end, 0),
        over_under=round(over_under, 0),
        last_sync=store.data.last_sync,
        last_odometer=last_odometer,
    )


# --- Forecast ---


@api.get("/forecast", response_model=ForecastOut, operation_id="getForecast")
async def get_forecast(store: DataStoreDep, model: str = "linear"):
    config = store.data.lease_config
    if not config:
        raise HTTPException(status_code=400, detail="No lease configured")

    readings = store.data.readings
    if len(readings) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 3 readings for forecast (have {len(readings)})",
        )

    try:
        if model == "prophet":
            return forecast_timeseries(readings, config)
        else:
            return forecast_linear(readings, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
