from databricks.sdk import WorkspaceClient

from .models import ForecastOut, LeaseConfig, MileageReading


class ForecastService:
    """Routes forecast requests through a Databricks Model Serving endpoint.

    Initialized in FastAPI lifespan when TESLA_LEASE_TRACKER_FORECAST_ENDPOINT
    is set. Returns None from the dependency if the env var is absent (local dev),
    preserving unchanged local behavior via forecast_linear / forecast_timeseries.
    """

    def __init__(self, endpoint_name: str, ws: WorkspaceClient) -> None:
        self._endpoint = endpoint_name
        self._ws = ws

    def forecast(
        self,
        readings: list[MileageReading],
        config: LeaseConfig,
        model_type: str = "linear",
    ) -> ForecastOut:
        response = self._ws.serving_endpoints.query(
            name=self._endpoint,
            dataframe_records=[
                {
                    "model_type": model_type,
                    "lease_config_json": config.model_dump_json(),
                }
            ],
        )
        assert response.predictions is not None, "Model Serving returned no predictions"
        return ForecastOut.model_validate_json(response.predictions[0]["forecast_json"])
