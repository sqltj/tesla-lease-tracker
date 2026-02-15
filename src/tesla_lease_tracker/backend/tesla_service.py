import asyncio
import time

import aiohttp

from .logger import logger
from .runtime import Runtime


class TeslaServiceError(Exception):
    pass


class TeslaService:
    """Wraps Tesla Fleet API with Databricks-secret-based auth and token caching."""

    def __init__(self, runtime: Runtime) -> None:
        self._runtime = runtime
        self._config = runtime.config
        self._access_token: str | None = None
        self._token_expiry: float = 0

    def _get_secret(self, key: str) -> str:
        scope = self._config.tesla_secret_scope
        resp = self._runtime.ws.secrets.get_secret(scope, key)
        if resp.value is None:
            raise TeslaServiceError(f"Secret {scope}/{key} has no value")
        # Databricks returns base64-encoded bytes; decode to string
        import base64
        return base64.b64decode(resp.value).decode("utf-8")

    async def _ensure_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        client_id = self._get_secret(self._config.tesla_client_id_key)
        client_secret = self._get_secret(self._config.tesla_client_secret_key)
        refresh_token = self._get_secret(self._config.tesla_refresh_token_key)

        # Exchange refresh token for access token
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://auth.tesla.com/oauth2/v3/token",
                json={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                },
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise TeslaServiceError(
                        f"Tesla OAuth failed ({resp.status}): {body}. "
                        "If refresh token expired (90 days), update the Databricks secret."
                    )
                data = await resp.json()

        self._access_token = data["access_token"]
        # Cache token for slightly less than its actual expiry
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
        logger.info("Tesla access token refreshed successfully")
        return self._access_token

    async def fetch_odometer(self, vin: str) -> float:
        """Fetch current odometer reading. Retries on 429 with exponential backoff."""
        token = await self._ensure_access_token()
        region = self._config.tesla_api_region
        base_url = f"https://fleet-api.prd.{region}.vn.cloud.tesla.com"

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{base_url}/api/1/vehicles/{vin}/vehicle_data",
                        params={"endpoints": "vehicle_state"},
                        headers={"Authorization": f"Bearer {token}"},
                    ) as resp:
                        if resp.status == 200:
                            try:
                                data = await resp.json()
                                odometer = data["response"]["vehicle_state"]["odometer"]
                                logger.info(f"Fetched odometer for {vin}: {odometer}")
                                return float(odometer)
                            except (KeyError, TypeError, ValueError) as e:
                                body = await resp.text()
                                raise TeslaServiceError(
                                    f"Failed to parse Tesla API response: {str(e)}. Response: {body}"
                                )

                        if resp.status == 429 and attempt < max_retries:
                            wait = 2 ** attempt
                            logger.warning(f"Rate limited (429), retrying in {wait}s...")
                            await asyncio.sleep(wait)
                            continue

                        body = await resp.text()
                        raise TeslaServiceError(
                            f"Tesla API error ({resp.status}): {body}"
                        )
            except TeslaServiceError:
                raise
            except Exception as e:
                raise TeslaServiceError(f"Unexpected error calling Tesla API: {str(e)}")

        raise TeslaServiceError("Max retries exceeded for Tesla API")
