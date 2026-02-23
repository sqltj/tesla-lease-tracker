from collections.abc import Generator
from typing import Annotated

from databricks.sdk import WorkspaceClient
from fastapi import Depends, Header, HTTPException, Request
from sqlmodel import Session

from .config import AppConfig
from .data_store import DataStore
from .repositories import LeaseRepository, MileageRepository
from .runtime import Runtime
from .forecast_service import ForecastService
from .zerobus_service import ZerobusService


def get_config(request: Request) -> AppConfig:
    if not hasattr(request.app.state, "config"):
        raise RuntimeError(
            "AppConfig not initialized. "
            "Ensure app.state.config is set during application lifespan startup."
        )
    return request.app.state.config


ConfigDep = Annotated[AppConfig, Depends(get_config)]


def get_runtime(request: Request) -> Runtime:
    if not hasattr(request.app.state, "runtime"):
        raise RuntimeError(
            "Runtime not initialized. "
            "Ensure app.state.runtime is set during application lifespan startup."
        )
    return request.app.state.runtime


RuntimeDep = Annotated[Runtime, Depends(get_runtime)]


def get_data_store(config: ConfigDep, runtime: RuntimeDep) -> DataStore | None:
    if config.storage_mode == "json":
        return runtime.data_store
    return None


DataStoreDep = Annotated[DataStore | None, Depends(get_data_store)]


def get_db_session(
    config: ConfigDep, runtime: RuntimeDep
) -> Generator[Session | None, None, None]:
    if config.storage_mode == "database":
        with runtime.get_session() as session:
            yield session
    else:
        yield None


SessionDep = Annotated[Session | None, Depends(get_db_session)]


def get_lease_repo(session: SessionDep) -> LeaseRepository | None:
    if session is None:
        return None
    return LeaseRepository(session)


LeaseRepoDep = Annotated[LeaseRepository | None, Depends(get_lease_repo)]


def get_mileage_repo(session: SessionDep) -> MileageRepository | None:
    if session is None:
        return None
    return MileageRepository(session)


MileageRepoDep = Annotated[MileageRepository | None, Depends(get_mileage_repo)]


def get_zerobus_service(request: Request) -> ZerobusService | None:
    return getattr(request.app.state, "zerobus_service", None)


ZerobusServiceDep = Annotated[ZerobusService | None, Depends(get_zerobus_service)]


def get_forecast_service(request: Request) -> ForecastService | None:
    return getattr(request.app.state, "forecast_service", None)


ForecastServiceDep = Annotated[ForecastService | None, Depends(get_forecast_service)]


def get_obo_ws(
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
) -> WorkspaceClient:
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Forwarded-Access-Token header",
        )
    return WorkspaceClient(token=token, auth_type="pat")
