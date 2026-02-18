# Databricks Deployment Guide

Complete guide for deploying Tesla Lease Tracker to Databricks using Asset Bundles (DAB) with free edition serverless compute.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Configuration Steps](#configuration-steps)
- [Deployment](#deployment)
- [Post-Deployment Verification](#post-deployment-verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Databricks Workspace** (Free or Paid edition)
  - Free edition supports serverless compute
  - Paid edition recommended for production deployments
- **Databricks CLI** v0.210+ installed
  ```bash
  # Install or upgrade
  brew install databricks  # macOS
  # or
  curl https://raw.githubusercontent.com/databricks/cli/main/install.sh | sh  # Linux/WSL
  ```
- **Python 3.11+** with `uv`
  ```bash
  brew install uv  # or visit https://docs.astral.sh/uv/
  ```
- **Git** for version control

### Databricks Account Setup

1. **Create Databricks Workspace**
   - Visit [databricks.com](https://databricks.com)
   - Sign up for free edition or log in to existing account
   - Create workspace in preferred region

2. **Generate Personal Access Token**
   - In Databricks workspace, click Settings → User Settings → Developer Tools
   - Click "Generate new token"
   - Copy token (keep secure, never commit)

3. **Configure Databricks CLI**
   ```bash
   databricks configure --token
   # Paste token when prompted
   # Enter workspace URL: https://your-workspace-id.cloud.databricks.com
   ```

4. **Verify Configuration**
   ```bash
   databricks workspace ls /
   # Should list workspace contents without errors
   ```

## Configuration Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/sqltj/tesla-lease-tracker.git
cd tesla-lease-tracker
```

### Step 2: Set Workspace Host Variable

The DAB configuration uses a variable for workspace URL to support multiple environments. Replace the placeholder with your actual workspace URL.

**Option A: Using Environment Variable (Recommended)**

```bash
export DATABRICKS_WORKSPACE_HOST="https://your-workspace-id.cloud.databricks.com"

# Verify it's set
echo $DATABRICKS_WORKSPACE_HOST
```

**Option B: Update databricks.yml Directly**

```yaml
# In databricks.yml, update variables section:
variables:
  workspace_host:
    description: "Databricks workspace URL"
    default: "https://your-workspace-id.cloud.databricks.com"  # Replace this
```

### Step 3: Update Alert Email Addresses

Configure where to send anomaly detection alerts.

In `databricks.yml`, update each target with actual email:

```yaml
targets:
  dev:
    variables:
      alert_email: "your-email@company.com"  # Replace this

  staging:
    variables:
      alert_email: "ops-team@company.com"    # Replace this

  prod-na:
    variables:
      alert_email: "alerts@company.com"      # Replace this
```

### Step 4: Validate Configuration

Run the validation script to catch configuration issues before deployment:

```bash
# Install dependencies
uv add databricks-sdk pyyaml

# Run validation
uv run python scripts/validate_dab_config.py

# With specific profile
uv run python scripts/validate_dab_config.py --profile production

# Skip workspace connection check
uv run python scripts/validate_dab_config.py --skip-workspace
```

**Expected output:**
```
✅ VALIDATION PASSED

✓ Checking for placeholder values...
  No placeholders found
✓ Checking required variables...
  All required variables defined
✓ Checking resource configuration...
  Resources configured correctly
✓ Checking jobs use serverless compute...
  All jobs configured for serverless
✓ Connecting to Databricks workspace...
  Connected to workspace
```

## Deployment

### Step 1: Build Application

```bash
uv run apx build
```

This builds the FastAPI backend and React frontend into `.build/` directory.

### Step 2: Validate Bundle

```bash
databricks bundle validate
```

Should show:
```
Validation OK
```

### Step 3: Deploy to Dev (First Time)

```bash
# Deploy to dev environment
databricks bundle deploy -t dev

# Verbose output for debugging
databricks bundle deploy -t dev -v
```

**What happens:**
- SQL warehouse created (may take 2-5 minutes)
- Jobs registered in Databricks workspace
- App deployed to Databricks Apps service

### Step 4: Deploy to Other Environments

```bash
# Staging
databricks bundle deploy -t staging

# Production - North America
databricks bundle deploy -t prod-na

# Production - Europe
databricks bundle deploy -t prod-eu

# Production - China
databricks bundle deploy -t prod-cn
```

### Dry-Run Deployment (Testing)

To see what would be deployed without actually deploying:

```bash
databricks bundle deploy -t dev --dry-run
```

## Post-Deployment Verification

### 1. Verify SQL Warehouse Created

```bash
# List all warehouses
databricks sql warehouses list

# Should show: tesla-lease-tracker-warehouse-dev
# Status should be "RUNNING" or "STARTING"
```

### 2. Verify Jobs Created

```bash
# List all jobs
databricks jobs list

# Should show 4 jobs:
# - Tesla Lease Tracker - Setup Infrastructure
# - [dev] Tesla Lease Tracker - Weekly Backup
# - [dev] Tesla Lease Tracker - Data Quality Alerts
# - [dev] Tesla Lease Tracker - Optimize Storage (Weekly Vacuum)
```

### 3. Run Setup Infrastructure Manually

```bash
# Find the job ID
JOB_ID=$(databricks jobs list | grep "Setup Infrastructure" | awk '{print $1}')

# Run the job
databricks jobs run-now --job-id $JOB_ID

# Check job run status
databricks jobs get-run --run-id <run_id>

# View job logs
databricks jobs get-run-output --run-id <run_id>
```

### 4. Verify App Deployed

```bash
# List deployed apps
databricks apps list

# Should show: tesla-lease-tracker
# Status should be "READY"

# Get app URL
databricks apps get tesla-lease-tracker
```

### 5. Test Data Flow

```bash
# Connect to workspace and query the Delta table
databricks sql <<EOF
SELECT COUNT(*) as mileage_count FROM default.tesla_mileage_readings;
SELECT MAX(recorded_at) as latest_reading FROM default.tesla_mileage_readings;
EOF
```

## Monitoring

### Check Scheduled Job Status

```bash
# Get all job runs
databricks jobs list-runs --job-id <job_id>

# Monitor specific job run
databricks jobs get-run --run-id <run_id> --verbose
```

### View Warehouse Usage

In Databricks workspace:
1. Click "SQL" in left sidebar
2. Click "SQL Warehouses"
3. Click "tesla-lease-tracker-warehouse-dev"
4. View query history and resource usage

### Check Alert Configuration

In `databricks.yml`, alerts are sent when anomalies detected via:
- Databricks SQL Alerts (real-time)
- Scheduled job notifications (30-minute intervals)

## Troubleshooting

### Issue: "REPLACE_WITH_" placeholders in validation error

**Solution:**
```bash
# Make sure you've set workspace_host and email variables
export DATABRICKS_WORKSPACE_HOST="https://your-workspace.cloud.databricks.com"

# Update databricks.yml with actual values
# Then re-validate
uv run python scripts/validate_dab_config.py
```

### Issue: "Workspace connection failed"

**Solution:**
1. Verify Databricks CLI is configured:
   ```bash
   databricks workspace ls /
   ```
2. Check token is valid (tokens expire after 90 days)
3. Use specific profile if you have multiple:
   ```bash
   uv run python scripts/validate_dab_config.py --profile <profile_name>
   ```

### Issue: "SQL warehouse not found" during deployment

**Solution:**
- This is normal on first deployment. Warehouse is created automatically.
- Wait 2-5 minutes for warehouse to be ready
- Check status: `databricks sql warehouses list`
- If still pending after 10 minutes, check workspace resource limits

### Issue: Job run fails with notebook not found error

**Solution:**
1. Verify notebooks exist in workspace:
   ```bash
   databricks workspace ls /Users/$(databricks workspace ls / | grep $(whoami) | awk '{print $NF}')
   ```
2. Check notebook paths in databricks.yml match workspace structure
3. Ensure `.build/` directory was built: `uv run apx build`

### Issue: Serverless compute not available in free edition

**Solution:**
- Free edition has limited serverless compute hours
- Current configuration uses 2X-Small warehouse (minimal cost)
- For production, upgrade to paid Databricks edition
- See [Databricks Free Edition Limitations](https://docs.databricks.com/getting-started/free-edition-limitations)

### Issue: Deployment times out

**Solution:**
```bash
# Increase timeout and retry
databricks bundle deploy -t dev --var timeout_seconds=3600

# Or check deployment status separately
databricks bundle status
```

## Advanced: Multi-Profile Deployment

If you manage multiple Databricks workspaces (dev, staging, prod):

### Setup Multiple Profiles

```bash
# Profile 1: Development
databricks configure --token --profile dev
# Enter: workspace URL for dev environment

# Profile 2: Production
databricks configure --token --profile prod
# Enter: workspace URL for production environment
```

### Deploy with Specific Profile

```bash
# Deploy to dev workspace
databricks bundle deploy -t dev --profile dev

# Deploy to prod workspace
databricks bundle deploy -t prod-na --profile prod
```

## Best Practices

1. **Validate before deploying:**
   ```bash
   uv run python scripts/validate_dab_config.py
   ```

2. **Test in dev first:**
   ```bash
   databricks bundle deploy -t dev
   # Verify successful
   # Then deploy to higher environments
   ```

3. **Keep secrets secure:**
   - Never commit `databricks.yml` with real workspace URLs or credentials
   - Use environment variables: `DATABRICKS_WORKSPACE_HOST`
   - Use `.gitignore` for local config overrides

4. **Monitor scheduled jobs:**
   - Set up email alerts for failed jobs
   - Review warehouse usage to optimize costs
   - Archive old job logs regularly

5. **Backup configurations:**
   ```bash
   # Export current deployment
   databricks bundle export > bundle-$(date +%Y%m%d).json
   ```

## Support & Resources

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/en/dev-tools/bundles/)
- [Databricks CLI Reference](https://docs.databricks.com/en/dev-tools/cli/)
- [Databricks Free Edition Guide](https://docs.databricks.com/getting-started/free-edition-limitations)
- [Serverless SQL Warehouses](https://docs.databricks.com/compute/sql-warehouse/serverless.html)

## Related Documentation

- [DEPLOYMENT_ROADMAP.md](../DEPLOYMENT_ROADMAP.md) - Overall deployment strategy
- [README.md](../README.md) - Project overview and quick start
