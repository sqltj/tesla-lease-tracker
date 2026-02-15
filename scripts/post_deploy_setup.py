#!/usr/bin/env python3
"""
Run post-deployment infrastructure setup.

This script executes the setup job to create Lakebase instance and Delta table
after 'databricks bundle deploy' completes.

Usage:
    After: uv run apx build && databricks bundle deploy -p <profile>
    Run: uv run python scripts/post_deploy_setup.py --profile <your-profile>
"""

import argparse
import sys
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunNow


def find_setup_job(ws: WorkspaceClient) -> int:
    """Find the setup infrastructure job in the workspace."""
    print("\n1. Finding setup infrastructure job...")

    try:
        # List jobs with the specific name
        jobs_list = ws.jobs.list(
            filter='name = "Tesla Lease Tracker - Setup Infrastructure"'
        )

        for job in jobs_list:
            print(f"   ✓ Found job: {job.job_id} - {job.settings.name}")
            return job.job_id

        print("   ❌ Setup job not found in workspace")
        print(
            "   → Make sure to run: databricks bundle deploy -p <profile>"
        )
        return None

    except Exception as e:
        print(f"   ❌ Error finding job: {e}")
        return None


def run_setup_job(ws: WorkspaceClient, job_id: int) -> bool:
    """Run setup infrastructure job and wait for completion."""
    print(f"\n2. Starting setup job {job_id}...")

    try:
        # Trigger the job
        run_response = ws.jobs.run_now(job_id=job_id)
        run_id = run_response.run_id

        print(f"   ✓ Job started (run_id: {run_id})")
        print("   → Waiting for completion...")

        # Poll for completion
        start_time = time.time()
        poll_interval = 5
        timeout = 600  # 10 minutes

        while time.time() - start_time < timeout:
            run = ws.jobs.get_run(run_id=run_id)
            state = run.state

            if state.life_cycle_state == "TERMINATED":
                if state.state_message == "":
                    print(f"   ✓ Job completed successfully")
                    return True
                else:
                    print(f"   ⚠ Job terminated with message: {state.state_message}")
                    return True
            elif state.life_cycle_state == "INTERNAL_ERROR":
                print(f"   ❌ Job failed with internal error")
                print(f"   → Check logs in Databricks workspace")
                return False
            else:
                elapsed = int(time.time() - start_time)
                print(f"   → Status: {state.life_cycle_state}... ({elapsed}s)")
                time.sleep(poll_interval)

        print(f"   ⚠ Job did not complete within {timeout} seconds")
        print(f"   → Check Databricks UI for status")
        return False

    except Exception as e:
        print(f"   ❌ Error running job: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run post-deployment infrastructure setup for Tesla Lease Tracker"
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Databricks CLI profile to use for authentication",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Maximum seconds to wait for job completion (default: 600)",
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("🔧 Tesla Lease Tracker - Post-Deployment Infrastructure Setup")
    print("=" * 70)

    try:
        # Connect to workspace
        ws = WorkspaceClient(profile=args.profile)
        print(f"\n✓ Connected to Databricks workspace (profile: {args.profile})")

    except Exception as e:
        print(f"\n❌ Failed to connect to Databricks workspace")
        print(f"   Error: {e}")
        print(f"\n   Verify Databricks CLI is configured:")
        print(f"   databricks configure --profile {args.profile}")
        sys.exit(1)

    # Find setup job
    job_id = find_setup_job(ws)
    if not job_id:
        sys.exit(1)

    # Run setup job
    if not run_setup_job(ws, job_id):
        sys.exit(1)

    # Success!
    print("\n" + "=" * 70)
    print("✅ Infrastructure setup complete!")
    print("=" * 70)
    print("\n📋 Next steps:")
    print("   1. Open your deployed app")
    print("   2. Configure your Tesla lease details")
    print("   3. Register with Tesla Fleet API (if using real data)")
    print("      uv run python scripts/register_fleet_api.py \\")
    print("        --domain <your-deployed-domain>")
    print("\n💡 To test with sample data locally:")
    print("   uv run apx dev start")
    print("   uv run python scripts/seed_local.py")


if __name__ == "__main__":
    main()
