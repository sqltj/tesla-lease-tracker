from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .._metadata import app_name, dist_dir
from .config import AppConfig
from .middleware import RequestLoggingMiddleware
from .router import api
from .runtime import Runtime
from .utils import add_not_found_handler
from .logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = AppConfig()
    logger.info(f"Starting app with configuration:\n{config}")

    runtime = Runtime(config)
    app.state.config = config
    app.state.runtime = runtime

    from .metrics_service import MetricsCollector
    app.state.metrics = MetricsCollector()
    logger.info("MetricsCollector initialized")

    # Initialize Tesla service (token cache is preserved across requests)
    from .tesla_service import TeslaService

    try:
        app.state.tesla_service = TeslaService(runtime)
        logger.info("TeslaService initialized")
    except Exception as e:
        logger.warning(f"TeslaService init failed (non-fatal): {e}")
        app.state.tesla_service = None

    zerobus_service = None

    if config.storage_mode == "database":
        runtime.validate_db()
        runtime.initialize_models()
        logger.info("Database storage initialized")

        # Start Zerobus for streaming mileage to Delta table
        try:
            from .zerobus_service import ZerobusService

            table_name = f"{config.zerobus_catalog}.{config.zerobus_schema}.mileage_readings"
            zerobus_service = ZerobusService(
                server_endpoint=runtime.ws.config.host.replace(
                    "https://", ""
                ).replace("/", "")
                + ".zerobus."
                + runtime.ws.config.host.split(".")[-3]
                + ".cloud.databricks.com",
                workspace_url=runtime.ws.config.host,
                client_id=runtime.ws.config.client_id or "",
                client_secret=runtime.ws.config.client_secret or "",
                table_name=table_name,
            )
            await zerobus_service.start()
            app.state.zerobus_service = zerobus_service
        except Exception as e:
            logger.warning(f"Zerobus initialization failed (non-fatal): {e}")
            app.state.zerobus_service = None

        if config.forecast_endpoint:
            try:
                from .forecast_service import ForecastService

                app.state.forecast_service = ForecastService(
                    endpoint_name=config.forecast_endpoint,
                    ws=runtime.ws,
                )
                logger.info(f"ForecastService initialized: {config.forecast_endpoint}")
            except Exception as e:
                logger.warning(f"ForecastService init failed (non-fatal): {e}")
                app.state.forecast_service = None
        else:
            app.state.forecast_service = None
    else:
        # JSON fallback mode
        Path(config.data_file_path).parent.mkdir(parents=True, exist_ok=True)
        logger.info("JSON file storage initialized")

    yield

    # Shutdown
    if zerobus_service:
        await zerobus_service.close()


app = FastAPI(title=f"{app_name}", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
ui = StaticFiles(directory=dist_dir, html=True)

app.include_router(api)
app.mount("/", ui)

add_not_found_handler(app)
