from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tesla_lease_tracker.backend.zerobus_service import ZerobusService


@pytest.fixture
def service():
    return ZerobusService(
        server_endpoint="test.zerobus.us-west-2.cloud.databricks.com",
        workspace_url="https://test.cloud.databricks.com",
        client_id="test-client-id",
        client_secret="test-secret",
        table_name="main.default.mileage_readings",
    )


class TestZerobusService:
    @pytest.mark.asyncio
    async def test_ingest_skipped_when_stream_not_started(self, service):
        """Ingest should be a no-op when stream hasn't been initialized."""
        await service.ingest_reading(
            vin="5YJ3E1EA1NF123456",
            timestamp="2024-03-01T10:00:00",
            odometer=1500.0,
        )
        # Should not raise — just logs a warning

    @pytest.mark.asyncio
    async def test_ingest_calls_stream(self, service):
        """When stream is available, ingest_reading should call stream.ingest_record."""
        import asyncio

        mock_stream = AsyncMock()
        # ingest_record is async and returns a future that is then awaited
        resolved_future = asyncio.get_event_loop().create_future()
        resolved_future.set_result(None)
        mock_stream.ingest_record = AsyncMock(return_value=resolved_future)
        service._stream = mock_stream

        await service.ingest_reading(
            vin="5YJ3E1EA1NF123456",
            timestamp="2024-03-01T10:00:00",
            odometer=1500.0,
        )

        mock_stream.ingest_record.assert_awaited_once_with(
            {"vin": "5YJ3E1EA1NF123456", "timestamp": "2024-03-01T10:00:00", "odometer": 1500.0}
        )

    @pytest.mark.asyncio
    async def test_ingest_handles_error_gracefully(self, service):
        """Ingest errors should be caught, not raised."""
        mock_stream = AsyncMock()
        mock_stream.ingest_record.side_effect = RuntimeError("Connection lost")
        service._stream = mock_stream

        # Should not raise
        await service.ingest_reading(
            vin="5YJ3E1EA1NF123456",
            timestamp="2024-03-01T10:00:00",
            odometer=1500.0,
        )

    @pytest.mark.asyncio
    async def test_close_when_no_stream(self, service):
        """Close should be safe when stream was never started."""
        await service.close()

    @pytest.mark.asyncio
    async def test_close_calls_stream_close(self, service):
        """Close should close the stream when it exists."""
        mock_stream = AsyncMock()
        service._stream = mock_stream

        await service.close()

        mock_stream.close.assert_awaited_once()
        assert service._stream is None

    @pytest.mark.asyncio
    async def test_start_failure_is_non_fatal(self, service):
        """If Zerobus SDK fails to initialize, start() should not raise."""
        with patch.dict("sys.modules", {"zerobus": None, "zerobus.sdk": None, "zerobus.sdk.aio": None}):
            await service.start()
            assert service._stream is None
