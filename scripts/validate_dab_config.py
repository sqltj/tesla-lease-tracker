#!/usr/bin/env python3
"""
Databricks Asset Bundle Configuration Validator

Validates DAB configuration for free edition compatibility before deployment.
Checks for:
- Placeholder values needing replacement
- Workspace connectivity
- Required resources and variables
- Notebook existence
"""

import argparse
import re
import sys
import yaml
from pathlib import Path
from typing import List, Tuple

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.core import Config
except ImportError:
    print("Error: databricks-sdk not installed. Install with: uv add databricks-sdk")
    sys.exit(1)


class DABValidator:
    """Validates Databricks Asset Bundle configuration."""

    def __init__(self, config_path: str = "databricks.yml", profile: str = None):
        """Initialize validator with DAB config path and Databricks profile."""
        self.config_path = Path(config_path)
        self.profile = profile
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config = {}
        self.ws_client = None

    def load_config(self) -> bool:
        """Load and parse databricks.yml."""
        if not self.config_path.exists():
            self.errors.append(f"Config file not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parse error: {e}")
            return False

    def connect_workspace(self) -> bool:
        """Establish connection to Databricks workspace."""
        try:
            # Try to use provided profile or default
            config_kwargs = {}
            if self.profile:
                config_kwargs["profile"] = self.profile

            self.ws_client = WorkspaceClient(**config_kwargs)
            # Test connection
            self.ws_client.workspace.get_status("/")
            return True
        except Exception as e:
            self.errors.append(f"Workspace connection failed: {e}")
            self.errors.append(
                "Ensure Databricks CLI is configured: databricks configure --token"
            )
            return False

    def check_placeholders(self) -> bool:
        """Scan configuration for placeholder values that need replacement."""
        placeholder_patterns = [
            (r"REPLACE_WITH_", "placeholder value"),
            (r"https://dbc-xxxx\.cloud\.databricks\.com", "example workspace URL"),
            (r"xxxx", "incomplete value"),
        ]

        config_str = yaml.dump(self.config)
        found_issues = False

        for pattern, description in placeholder_patterns:
            matches = re.finditer(pattern, config_str)
            for match in matches:
                # Find line number for better error reporting
                lines_before = config_str[:match.start()].count("\n")
                self.errors.append(
                    f"Line {lines_before + 1}: Found {description}: '{match.group()}'"
                )
                found_issues = True

        return not found_issues

    def check_variables(self) -> bool:
        """Verify all required variables are defined."""
        required_vars = ["workspace_host", "environment", "alert_email"]
        defined_vars = list(self.config.get("variables", {}).keys())

        missing = [v for v in required_vars if v not in defined_vars]
        if missing:
            self.errors.append(f"Missing required variables: {', '.join(missing)}")
            return False

        return True

    def check_resources(self) -> bool:
        """Verify required resources are configured."""
        resources = self.config.get("resources", {})

        # Check for SQL warehouse
        if "sql_warehouses" not in resources:
            self.errors.append("Missing sql_warehouses resource for serverless compute")
            return False

        # Check for jobs
        if "jobs" not in resources:
            self.warnings.append("No jobs defined in configuration")
            return True

        return True

    def check_jobs_serverless(self) -> bool:
        """Verify all jobs use serverless compute (no job_clusters)."""
        jobs = self.config.get("resources", {}).get("jobs", {})

        for job_name, job_config in jobs.items():
            # Check for legacy job_clusters (should not exist)
            if "job_clusters" in job_config:
                self.errors.append(
                    f"Job '{job_name}' uses deprecated job_clusters. "
                    "Must use serverless warehouse_id instead."
                )
                return False

            # Check tasks use warehouse_id or environment_key
            tasks = job_config.get("tasks", [])
            for task in tasks:
                if "sql_task" in task and "warehouse_id" not in task:
                    self.errors.append(
                        f"SQL task in job '{job_name}' missing warehouse_id"
                    )
                    return False

                if "notebook_task" in task and "environment_key" not in task:
                    # Check if it's Python or SQL by filename
                    notebook_path = task.get("notebook_task", {}).get("notebook_path", "")
                    if not notebook_path.endswith(".sql"):
                        if "job_cluster_key" in task:
                            self.errors.append(
                                f"Notebook task in job '{job_name}' "
                                "uses job_cluster_key instead of environment_key"
                            )
                            return False

        return True

    def check_notebooks_exist(self) -> bool:
        """Verify referenced notebooks exist in workspace."""
        if not self.ws_client:
            self.warnings.append("Skipping notebook existence check (no workspace connection)")
            return True

        jobs = self.config.get("resources", {}).get("jobs", {})
        workspace_status = None

        for job_name, job_config in jobs.items():
            tasks = job_config.get("tasks", [])
            for task in tasks:
                notebook_path = None

                if "notebook_task" in task:
                    notebook_path = task["notebook_task"].get("notebook_path", "")

                if "sql_task" in task:
                    sql_path = task["sql_task"].get("file", {}).get("path", "")
                    # Convert /Workspace/ path to regular path for checking
                    notebook_path = sql_path.replace("/Workspace", "")

                if notebook_path:
                    try:
                        self.ws_client.workspace.get_status(notebook_path)
                    except Exception as e:
                        self.warnings.append(
                            f"Could not verify notebook exists: {notebook_path} ({e})"
                        )

        return True

    def check_warehouse_exists(self) -> bool:
        """Verify SQL warehouse is available."""
        if not self.ws_client:
            self.warnings.append("Skipping warehouse check (no workspace connection)")
            return True

        try:
            # Get all warehouses
            warehouses = list(self.ws_client.warehouses.list())
            if not warehouses:
                self.warnings.append(
                    "No SQL warehouses found. DAB will create one during deployment."
                )
            return True
        except Exception as e:
            self.warnings.append(f"Could not verify SQL warehouses: {e}")
            return True

    def validate(self, skip_workspace: bool = False) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks."""
        print("Validating Databricks Asset Bundle configuration...")
        print()

        # Step 1: Load config
        if not self.load_config():
            return False, self.errors, self.warnings

        # Step 2: Check placeholders
        print("✓ Checking for placeholder values...")
        if not self.check_placeholders():
            print(f"  Found {len(self.errors)} placeholder issues")
        else:
            print("  No placeholders found")

        # Step 3: Check variables
        print("✓ Checking required variables...")
        if not self.check_variables():
            pass
        else:
            print("  All required variables defined")

        # Step 4: Check resources
        print("✓ Checking resource configuration...")
        if not self.check_resources():
            pass
        else:
            print("  Resources configured correctly")

        # Step 5: Check jobs are serverless
        print("✓ Checking jobs use serverless compute...")
        if not self.check_jobs_serverless():
            pass
        else:
            print("  All jobs configured for serverless")

        # Step 6: Workspace-dependent checks (if enabled)
        if not skip_workspace:
            print("✓ Connecting to Databricks workspace...")
            if self.connect_workspace():
                print(f"  Connected to workspace")

                print("✓ Verifying SQL warehouse...")
                self.check_warehouse_exists()

                print("✓ Checking notebook references...")
                self.check_notebooks_exist()
            else:
                print("  Workspace connection failed (skipping workspace checks)")

        success = len(self.errors) == 0
        return success, self.errors, self.warnings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Databricks Asset Bundle configuration for free edition"
    )
    parser.add_argument(
        "--config",
        default="databricks.yml",
        help="Path to databricks.yml configuration file",
    )
    parser.add_argument(
        "--profile",
        help="Databricks CLI profile to use for workspace connection",
    )
    parser.add_argument(
        "--skip-workspace",
        action="store_true",
        help="Skip workspace-dependent checks (placeholders only)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress output, exit code only"
    )

    args = parser.parse_args()

    # Run validator
    validator = DABValidator(config_path=args.config, profile=args.profile)
    success, errors, warnings = validator.validate(skip_workspace=args.skip_workspace)

    if not args.quiet:
        print()
        if errors:
            print("❌ VALIDATION FAILED")
            print()
            print("Errors:")
            for error in errors:
                print(f"  • {error}")
        else:
            print("✅ VALIDATION PASSED")

        if warnings:
            print()
            print("Warnings:")
            for warning in warnings:
                print(f"  ⚠ {warning}")

        print()
        if not success:
            print("Action Required:")
            print("  1. Review errors above")
            print("  2. Update databricks.yml with actual values")
            print("  3. Run validation again")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
