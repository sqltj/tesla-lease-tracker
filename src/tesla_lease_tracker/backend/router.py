from datetime import datetime
from typing import Annotated

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User as UserOut
from fastapi import APIRouter, Depends, HTTPException

from .._metadata import api_prefix
from .dependencies import (
    ConfigDep,
    DataStoreDep,
    ForecastServiceDep,
    LeaseRepoDep,
    MileageRepoDep,
    RuntimeDep,
    ZerobusServiceDep,
    get_obo_ws,
)
from .forecast import forecast_linear, forecast_timeseries
from .logger import logger
from .models import (
    DashboardOut,
    ForecastOut,
    HealthOut,
    LeaseConfig,
    LeaseConfigIn,
    LeaseConfigOut,
    MileageReading,
    MileageReadingOut,
    SeedResultOut,
    VersionOut,
)
from .tesla_service import TeslaService, TeslaServiceError
from .db_models import LeaseConfigDB, MileageReadingDB
from sqlmodel import delete

api = APIRouter(prefix=api_prefix)


@api.get("/version", response_model=VersionOut, operation_id="getVersion")
async def version():
    return VersionOut.from_metadata()


@api.get("/health", response_model=HealthOut, operation_id="getHealth")
async def health(
    config: ConfigDep,
    store: DataStoreDep,
    lease_repo: LeaseRepoDep,
    mileage_repo: MileageRepoDep,
):
    if config.storage_mode == "database":
        assert lease_repo is not None
        assert mileage_repo is not None
        lease = lease_repo.get_lease_config()
        count = mileage_repo.count()
        last_sync = lease_repo.get_last_sync()
    else:
        assert store is not None
        lease = store.data.lease_config
        count = len(store.data.readings)
        last_sync = store.data.last_sync

    return HealthOut(
        status="ok",
        version=VersionOut.from_metadata().version,
        has_lease=lease is not None,
        readings_count=count,
        last_sync=last_sync,
    )


@api.get("/current-user", response_model=UserOut, operation_id="getCurrentUser")
def me(obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)]):
    return obo_ws.current_user.me()


# --- Lease Config ---


@api.get("/lease", response_model=LeaseConfigOut | None, operation_id="getLease")
async def get_lease(config: ConfigDep, store: DataStoreDep, lease_repo: LeaseRepoDep):
    if config.storage_mode == "database":
        assert lease_repo is not None
        return lease_repo.get_lease_config()
    assert store is not None
    return store.data.lease_config


@api.put("/lease", response_model=LeaseConfigOut, operation_id="saveLease")
async def save_lease(
    lease_in: LeaseConfigIn,
    config: ConfigDep,
    store: DataStoreDep,
    lease_repo: LeaseRepoDep,
):
    if config.storage_mode == "database":
        assert lease_repo is not None
        return lease_repo.save_lease_config(lease_in)

    # JSON fallback
    assert store is not None
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


@api.get("/mileage", response_model=list[MileageReadingOut], operation_id="listMileage")
async def get_mileage(
    config: ConfigDep,
    store: DataStoreDep,
    lease_repo: LeaseRepoDep,
    mileage_repo: MileageRepoDep,
):
    if config.storage_mode == "database":
        assert lease_repo is not None
        assert mileage_repo is not None
        lease = lease_repo.get_lease_config()
        if not lease:
            return []
        readings = mileage_repo.get_readings(vin=lease.vin)
        return [
            MileageReadingOut(
                timestamp=r.timestamp,
                odometer=r.odometer,
                lease_miles=r.odometer - lease.start_odometer,
            )
            for r in readings
        ]

    # JSON fallback
    assert store is not None
    cfg = store.data.lease_config
    if not cfg:
        return []
    return [
        MileageReadingOut(
            timestamp=r.timestamp,
            odometer=r.odometer,
            lease_miles=r.odometer - cfg.start_odometer,
        )
        for r in store.data.readings
    ]


@api.post(
    "/mileage/sync", response_model=MileageReadingOut, operation_id="syncMileage"
)
async def sync_mileage(
    config: ConfigDep,
    store: DataStoreDep,
    runtime: RuntimeDep,
    lease_repo: LeaseRepoDep,
    mileage_repo: MileageRepoDep,
    zerobus: ZerobusServiceDep,
):
    if config.storage_mode == "database":
        assert lease_repo is not None
        lease = lease_repo.get_lease_config()
    else:
        assert store is not None
        lease = store.data.lease_config

    if not lease:
        raise HTTPException(status_code=400, detail="No lease configured")

    try:
        service = TeslaService(runtime)
        odometer = await service.fetch_odometer(lease.vin)
    except TeslaServiceError as e:
        error_msg = str(e)
        logger.error(f"Tesla sync error: {error_msg}")
        raise HTTPException(status_code=502, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during sync: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=502, detail=error_msg)

    now = datetime.utcnow()

    if config.storage_mode == "database":
        assert mileage_repo is not None
        assert lease_repo is not None
        mileage_repo.add_reading(vin=lease.vin, timestamp=now, odometer=odometer)
        lease_repo.set_last_sync(now)

        # Stream to Delta table (non-fatal)
        if zerobus:
            await zerobus.ingest_reading(
                vin=lease.vin,
                timestamp=now.isoformat(),
                odometer=odometer,
            )
    else:
        assert store is not None
        reading = MileageReading(timestamp=now, odometer=odometer)
        store.data.readings.append(reading)
        store.data.last_sync = now
        store.save()

    return MileageReadingOut(
        timestamp=now,
        odometer=odometer,
        lease_miles=odometer - lease.start_odometer,
    )


# --- Dashboard ---


@api.get(
    "/dashboard", response_model=DashboardOut | None, operation_id="getDashboard"
)
async def get_dashboard(
    config: ConfigDep,
    store: DataStoreDep,
    lease_repo: LeaseRepoDep,
    mileage_repo: MileageRepoDep,
):
    if config.storage_mode == "database":
        assert lease_repo is not None
        assert mileage_repo is not None
        cfg = lease_repo.get_lease_config()
        if not cfg:
            return None
        readings = mileage_repo.get_readings(vin=cfg.vin)
        last_sync = lease_repo.get_last_sync()
    else:
        assert store is not None
        cfg = store.data.lease_config
        if not cfg:
            return None
        readings = store.data.readings
        last_sync = store.data.last_sync

    start_odo = cfg.start_odometer
    today = datetime.utcnow().date()
    lease_start = cfg.lease_start_date
    lease_end = cfg.lease_end_date

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
    budget_daily_rate = cfg.mileage_limit / total_days if total_days > 0 else 0
    projected_end = daily_average * total_days
    over_under = projected_end - cfg.mileage_limit

    return DashboardOut(
        lease_miles_used=lease_miles_used,
        mileage_limit=cfg.mileage_limit,
        daily_average=round(daily_average, 1),
        budget_daily_rate=round(budget_daily_rate, 1),
        days_remaining=days_remaining,
        total_lease_days=total_days,
        projected_end_miles=round(projected_end, 0),
        over_under=round(over_under, 0),
        last_sync=last_sync,
        last_odometer=last_odometer,
    )


# --- Forecast ---


@api.get("/forecast", response_model=ForecastOut, operation_id="getForecast")
async def get_forecast(
    config: ConfigDep,
    store: DataStoreDep,
    lease_repo: LeaseRepoDep,
    mileage_repo: MileageRepoDep,
    forecast_service: ForecastServiceDep,
    model: str = "linear",
):
    if config.storage_mode == "database":
        assert lease_repo is not None
        assert mileage_repo is not None
        cfg = lease_repo.get_lease_config()
        if not cfg:
            raise HTTPException(status_code=400, detail="No lease configured")
        readings = mileage_repo.get_readings(vin=cfg.vin)
    else:
        assert store is not None
        cfg = store.data.lease_config
        if not cfg:
            raise HTTPException(status_code=400, detail="No lease configured")
        readings = store.data.readings

    if len(readings) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 3 readings for forecast (have {len(readings)})",
        )

    try:
        if forecast_service:
            return forecast_service.forecast(readings, cfg, model_type=model)
        elif model == "prophet":
            return forecast_timeseries(readings, cfg)
        else:
            return forecast_linear(readings, cfg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api.post("/seed-local-data", response_model=SeedResultOut, operation_id="seedLocalData")
async def seed_local_data(
    config: ConfigDep,
    lease_repo: LeaseRepoDep,
    mileage_repo: MileageRepoDep,
    force: bool = False,
):
    """DEV ONLY: Seed database with realistic sample Tesla lease data.

    Only available when running locally (APX_DEV_DB_PORT set).
    """
    import os
    from datetime import date, timedelta

    # Only allow in dev mode
    if not os.environ.get("APX_DEV_DB_PORT"):
        raise HTTPException(status_code=403, detail="Seed endpoint only available in dev mode")

    if config.storage_mode != "database":
        raise HTTPException(status_code=400, detail="Seed endpoint requires database storage mode")

    assert lease_repo is not None
    assert mileage_repo is not None

    # Check if data already exists (skip check if force=True)
    existing = lease_repo.get_lease_config()
    if existing and not force:
        raise HTTPException(
            status_code=409,
            detail="Database already contains lease data. Use POST /api/seed-local-data?force=true to reset.",
        )

    # 3-year Tesla Model Y lease: Jun 2024 → May 2027, 36k miles
    lease_config = LeaseConfigIn(
        vin="5YJ3E1EA1NF123456",
        lease_start_date=date(2024, 6, 1),
        lease_end_date=date(2027, 5, 31),
        mileage_limit=36000,
        start_odometer=12.0,
    )
    lease_repo.save_lease_config(lease_config)

    # If force=True, clear old readings first
    if force:
        lease_repo.session.exec(delete(MileageReadingDB))

    # 19 readings from Jul 2024 → Feb 2026 (~18 months, ~18,000 lease miles)
    readings_data = [
        (datetime(2024, 7, 15, 14, 30), 924.3),
        (datetime(2024, 8, 10, 9, 15), 1847.6),
        (datetime(2024, 9, 5, 16, 45), 2623.1),
        (datetime(2024, 10, 1, 11, 20), 3398.7),
        (datetime(2024, 10, 28, 13, 50), 4289.2),
        (datetime(2024, 11, 22, 10, 30), 5067.8),
        (datetime(2024, 12, 18, 15, 0), 5946.4),
        (datetime(2025, 1, 12, 12, 40), 6734.9),
        (datetime(2025, 2, 8, 14, 10), 7678.5),
        (datetime(2025, 3, 5, 11, 55), 8512.1),
        (datetime(2025, 4, 1, 9, 30), 9289.6),
        (datetime(2025, 4, 28, 16, 20), 10178.3),
        (datetime(2025, 5, 25, 13, 45), 10967.8),
        (datetime(2025, 6, 20, 10, 15), 11834.2),
        (datetime(2025, 7, 17, 14, 50), 12689.7),
        (datetime(2025, 8, 13, 11, 30), 13523.4),
        (datetime(2025, 9, 9, 15, 10), 14456.9),
        (datetime(2025, 10, 6, 12, 25), 15267.5),
        (datetime(2026, 2, 14, 10, 0), 18123.7),
    ]

    for ts, odometer in readings_data:
        mileage_repo.add_reading(lease_config.vin, ts, odometer)

    # Update last sync
    lease_repo.set_last_sync(readings_data[-1][0])

    return SeedResultOut(
        status="success",
        lease_vin=lease_config.vin,
        readings_count=len(readings_data),
        odometer_range=f"{readings_data[0][1]:.1f} - {readings_data[-1][1]:.1f} miles",
    )
