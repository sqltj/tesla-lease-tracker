"""
Integration tests for Databricks deployment verification.

These tests require a live Databricks workspace connection.
Run with: uv run pytest tests/backend/test_deployment.py -v

Skip in CI or local runs without workspace access:
    uv run pytest -m "not requires_workspace"
"""

import pytest

pytestmark = pytest.mark.requires_workspace


def test_catalog_exists():
    """Verify main catalog exists in workspace."""
    from databricks.sdk import WorkspaceClient

    ws = WorkspaceClient()
    catalog_names = [c.name for c in ws.catalogs.list()]
    assert "main" in catalog_names


def test_bronze_schema_exists():
    """Verify bronze schema exists."""
    from databricks.sdk import WorkspaceClient

    ws = WorkspaceClient()
    schema_names = [s.name for s in ws.schemas.list(catalog_name="main")]
    assert "bronze_tesla_lease_tracker" in schema_names


def test_silver_schema_exists():
    """Verify silver schema exists."""
    from databricks.sdk import WorkspaceClient

    ws = WorkspaceClient()
    schema_names = [s.name for s in ws.schemas.list(catalog_name="main")]
    assert "silver_tesla_lease_tracker" in schema_names


def test_gold_schema_exists():
    """Verify gold schema exists."""
    from databricks.sdk import WorkspaceClient

    ws = WorkspaceClient()
    schema_names = [s.name for s in ws.schemas.list(catalog_name="main")]
    assert "gold_tesla_lease_tracker" in schema_names


def test_bronze_metadata_volume_exists():
    """Verify metadata volume exists in bronze schema."""
    from databricks.sdk import WorkspaceClient

    ws = WorkspaceClient()
    volume_names = [
        v.name
        for v in ws.volumes.list(
            catalog_name="main",
            schema_name="bronze_tesla_lease_tracker",
        )
    ]
    assert "metadata" in volume_names


def test_bronze_artifacts_volume_exists():
    """Verify artifacts volume exists in bronze schema."""
    from databricks.sdk import WorkspaceClient

    ws = WorkspaceClient()
    volume_names = [
        v.name
        for v in ws.volumes.list(
            catalog_name="main",
            schema_name="bronze_tesla_lease_tracker",
        )
    ]
    assert "artifacts" in volume_names
