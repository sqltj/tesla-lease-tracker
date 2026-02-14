from __future__ import annotations

from .logger import logger


class ZerobusService:
    """Streams mileage readings to a Delta table via Zerobus Ingest.

    Non-fatal: if Zerobus fails, we log errors but don't fail the request.
    Lakebase is the primary store; Zerobus is for analytics.
    """

    def __init__(
        self,
        server_endpoint: str,
        workspace_url: str,
        client_id: str,
        client_secret: str,
        table_name: str,
    ) -> None:
        self._server_endpoint = server_endpoint
        self._workspace_url = workspace_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._table_name = table_name
        self._sdk = None
        self._stream = None

    async def start(self) -> None:
        try:
            from zerobus.sdk.aio import ZerobusSdk
            from zerobus.sdk.shared import (
                RecordType,
                StreamConfigurationOptions,
                TableProperties,
            )

            self._sdk = ZerobusSdk(self._server_endpoint, self._workspace_url)
            table_props = TableProperties(self._table_name)
            options = StreamConfigurationOptions(record_type=RecordType.JSON)
            self._stream = await self._sdk.create_stream(
                self._client_id, self._client_secret, table_props, options
            )
            logger.info(f"Zerobus stream started for table {self._table_name}")
        except Exception as e:
            logger.error(f"Failed to start Zerobus stream: {e}")
            self._stream = None

    async def ingest_reading(
        self, vin: str, timestamp: str, odometer: float
    ) -> None:
        if not self._stream:
            logger.warning("Zerobus stream not available, skipping ingest")
            return
        try:
            record = {"vin": vin, "timestamp": timestamp, "odometer": odometer}
            future = await self._stream.ingest_record(record)
            await future
        except Exception as e:
            logger.error(f"Zerobus ingest failed (non-fatal): {e}")

    async def close(self) -> None:
        if self._stream:
            try:
                await self._stream.close()
                logger.info("Zerobus stream closed")
            except Exception as e:
                logger.error(f"Error closing Zerobus stream: {e}")
            self._stream = None
        self._sdk = None
