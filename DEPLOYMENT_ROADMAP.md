# Deployment Roadmap: Infrastructure as Code via DAB

## Overview

Currently, infrastructure setup (Lakebase, Delta tables) requires manual CLI commands. This plan moves to a fully automated, Infrastructure-as-Code approach using Databricks Asset Bundles (DAB).

## Phase 1: DAB-Based Infrastructure (Planned)

### Goal
Automate all post-deployment infrastructure setup via Databricks notebooks and DAB resources.

### Current State
```
Deploy (bundle deploy)
  ↓
Manual Steps:
  1. Create Lakebase instance
  2. Create Delta table
  3. Register Fleet API
```

### Target State
```
Deploy (bundle deploy)
  ↓
Automated Post-Deploy:
  1. Run DAB init jobs/notebooks
  2. Lakebase auto-created
  3. Delta table auto-created
  4. Run registration script
```

---

## Implementation Plan

### Step 1: Create Infrastructure Notebooks

**Location**: `databricks/notebooks/setup/`

#### `1_create_lakebase.py` (Databricks notebook)
```python
# Databricks notebook source
# Create Lakebase instance

from databricks.sdk import WorkspaceClient

ws = WorkspaceClient()

instance_name = "tesla-lease-tracker"
capacity = "SMALL"

# Create Lakebase instance via workspace APIs
# (Implementation details based on Databricks SDK)

print(f"✓ Lakebase instance created: {instance_name}")
```

#### `2_create_delta_table.sql` (SQL notebook)
```sql
-- Databricks notebook source
-- Create mileage_readings Delta table for Zerobus streaming

CREATE TABLE IF NOT EXISTS main.default.mileage_readings (
    vin STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    odometer DOUBLE NOT NULL
) USING DELTA;

COMMENT ON TABLE main.default.mileage_readings IS
  'Mileage readings streamed from Tesla Fleet API via Zerobus';

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_vin_timestamp
  ON main.default.mileage_readings (vin, timestamp);

SELECT COUNT(*) as table_size FROM main.default.mileage_readings;
```

### Step 2: Update `databricks.yml`

Add DAB resources to orchestrate setup:

```yaml
resources:
  jobs:
    setup_infrastructure:
      name: Tesla Lease Tracker - Setup Infrastructure
      description: One-time setup job for Lakebase and Delta tables
      tasks:
        - task_key: create_lakebase
          notebook_task:
            notebook_path: /tesla-lease-tracker/setup/1_create_lakebase
          existing_cluster_id: <cluster-id>

        - task_key: create_delta_table
          notebook_task:
            notebook_path: /tesla-lease-tracker/setup/2_create_delta_table
          depends_on:
            - task_key: create_lakebase
          existing_cluster_id: <cluster-id>

      job_clusters:
        - job_cluster_key: setup_cluster
          new_cluster:
            spark_version: "15.3.x-scala2.12"
            node_type_id: "i3.xlarge"
            num_workers: 1
```

### Step 3: Create Post-Deploy Script

**Location**: `scripts/post_deploy_setup.py`

```python
#!/usr/bin/env python3
"""
Run post-deployment infrastructure setup.

Usage:
    After: databricks bundle deploy -p <profile>
    Run: uv run python scripts/post_deploy_setup.py --profile <profile>
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunNow
import time
import sys

def run_setup_job(ws, job_id):
    """Run setup infrastructure job and wait for completion."""
    print(f"Starting setup job {job_id}...")

    run_response = ws.jobs.run_now(job_id=job_id)
    run_id = run_response.run_id

    # Poll for completion
    while True:
        run = ws.jobs.get_run(run_id=run_id)
        state = run.state

        if state in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
            if state == "TERMINATED":
                print("✓ Setup job completed successfully")
                return True
            else:
                print(f"✗ Setup job failed with state: {state}")
                return False

        print(f"  Status: {state}...")
        time.sleep(5)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run post-deployment setup")
    parser.add_argument("--profile", required=True, help="Databricks CLI profile")
    args = parser.parse_args()

    ws = WorkspaceClient(profile=args.profile)

    print("🔧 Tesla Lease Tracker - Post-Deployment Setup")
    print("=" * 60)

    # Find the setup job
    jobs = ws.jobs.list(filter='name = "Tesla Lease Tracker - Setup Infrastructure"')
    job = next(jobs, None)

    if not job:
        print("✗ Setup job not found in workspace")
        print("  Make sure to run: databricks bundle deploy -p <profile>")
        sys.exit(1)

    # Run the job
    if run_setup_job(ws, job.job_id):
        print("\n✓ Infrastructure setup complete!")
        print("\nNext steps:")
        print("1. Fleet API Registration:")
        print("   uv run python scripts/register_fleet_api.py --domain <your-domain>")
        print("\n2. Open your app and configure a lease")
        print("3. Wait for Fleet API approval (~1-24 hours)")
    else:
        print("\n✗ Setup failed. Check job logs in Databricks workspace.")
        sys.exit(1)
```

### Step 4: Update README

Add new deployment flow section:

```markdown
### 4. Run Post-Deployment Setup

Automatically provision Lakebase and Delta tables:

```bash
uv run python scripts/post_deploy_setup.py --profile <your-profile>
```

This runs the setup job which:
- Creates Lakebase instance
- Creates Delta table
- Indexes tables for performance
- Provides status updates

Wait for completion (~5-10 minutes).
```

### Step 5: Create Fleet API Registration Integration

Optional: Integrate Fleet API registration into setup job or separate step:

```python
# In post_deploy_setup.py, after infrastructure is ready
print("\nNext: Register with Tesla Fleet API")
subprocess.run([
    sys.executable,
    "scripts/register_fleet_api.py",
    "--domain", args.domain,
    "--region", args.region or "na"
])
```

---

## Timeline & Effort

| Phase | Task | Effort | Priority |
|-------|------|--------|----------|
| Phase 1 | Create infrastructure notebooks | 2-4 hours | High |
| Phase 1 | Update databricks.yml with jobs | 1-2 hours | High |
| Phase 1 | Create post_deploy_setup.py | 2-3 hours | High |
| Phase 1 | Update README | 1 hour | High |
| Phase 2 | Integrate Fleet API registration | 1-2 hours | Medium |
| Phase 2 | Add monitoring/alerts for setup jobs | 2-4 hours | Low |

---

## Benefits

✅ **Infrastructure as Code**: All setup captured in version-controlled DAB
✅ **Fully Automated**: One command after deployment
✅ **Idempotent**: Safe to re-run (CREATE IF NOT EXISTS)
✅ **Observable**: Job logs in Databricks workspace
✅ **Scalable**: Easy to add more setup tasks
✅ **Professional**: Industry-standard deployment pattern

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Job scheduling complexity | Use existing Databricks job framework (well-documented) |
| Failed job blocks deployment | Post-deploy is separate; users can troubleshoot in workspace |
| DAB complexity overhead | Keep notebooks simple; document purpose |
| Backwards compatibility | Keep manual CLI commands as fallback option |

---

## Success Criteria

- [ ] DAB deployment includes setup jobs
- [ ] `post_deploy_setup.py` successfully creates Lakebase + Delta table
- [ ] README documents automated flow
- [ ] Setup completes within 15 minutes
- [ ] Job logs are clear and actionable
- [ ] Manual commands still work as fallback

---

## Future Enhancements

- **Phase 2**: Add Zerobus Delta table partitioning by date
- **Phase 2**: Add monitoring dashboard for mileage readings table
- **Phase 3**: Automated backups and retention policies
- **Phase 3**: Multi-region deployment support
