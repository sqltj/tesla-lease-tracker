# Deployment Checklist -- Free Tier Databricks

Step-by-step guide for deploying the Tesla Lease Tracker to a Databricks free tier workspace.

---

## 1. Pre-Deployment

- [ ] **Free tier workspace** -- Sign up at <https://www.databricks.com/try-databricks> if you do not already have one.
- [ ] **Databricks CLI authenticated** -- Run `databricks auth login --host <workspace-url>` and verify with `databricks auth token`.
- [ ] **Tesla OAuth secrets stored** -- Add `TESLA_CLIENT_ID`, `TESLA_CLIENT_SECRET`, and `TESLA_REFRESH_TOKEN` to your workspace secrets scope (or `.env` for local dev).
- [ ] **Repository cloned** -- `git clone` the repo and ensure you are on the target branch.
- [ ] **Python dependencies installed** -- Run `uv sync` from the repo root.
- [ ] **Update `databricks.yml` variables** -- Replace all `REPLACE_WITH_*` placeholders in `databricks.yml` with actual values (`workspace_host`, `alert_email`, etc.).
- [ ] **Validate DAB config** -- Run `uv run python scripts/validate_dab_config.py` to catch placeholder or structural issues before deploying.

## 2. Deploy Infrastructure

1. **Deploy the bundle to dev target:**

   ```bash
   databricks bundle deploy -t dev
   ```

2. **Verify deployment output** -- Confirm the CLI reports no errors. Expected resources:
   - App: `tesla-lease-tracker`
   - SQL Warehouse: `tesla-lease-tracker-warehouse-dev`
   - Jobs: `setup_infrastructure`, `ml_training_pipeline`, `backup_mileage_readings`, `anomaly_detection_alerts`, `vacuum_mileage_readings`
   - Pipeline: `ml_feature_pipeline`
   - Experiment: `forecast`

3. **Run the one-time setup job:**

   ```bash
   databricks bundle run setup_infrastructure -t dev
   ```

   This creates the Lakebase instance and the `mileage_readings` Delta table.

## 3. Post-Deployment Validation

1. **Run the deployment verification script:**

   ```bash
   uv run python scripts/verify_dab_deployment.py
   ```

   This checks that the expected catalog, schemas, and volumes exist in the workspace. All checks should show PASS.

2. **Verify catalog and schemas via SQL (optional):**

   Open a SQL editor in the Databricks workspace and run:

   ```sql
   SHOW SCHEMAS IN main;
   ```

   Confirm the following schemas exist:
   - `bronze_tesla_lease_tracker`
   - `silver_tesla_lease_tracker`
   - `gold_tesla_lease_tracker`

3. **Verify volumes exist (optional):**

   ```sql
   SHOW VOLUMES IN main.bronze_tesla_lease_tracker;
   ```

   Confirm `metadata` and `artifacts` volumes are listed.

4. **Verify the Delta table:**

   ```sql
   DESCRIBE TABLE main.default.mileage_readings;
   ```

5. **Check the app is accessible:**

   ```bash
   databricks apps get tesla-lease-tracker
   ```

## 4. Troubleshooting

### Authentication errors

| Symptom | Fix |
|---|---|
| `databricks auth token` returns an error | Re-run `databricks auth login --host <workspace-url>`. Ensure the workspace URL has no trailing slash. |
| `PERMISSION_DENIED` on deploy | Verify your user has workspace admin or contributor permissions. Free tier accounts are admin by default. |
| `InvalidParameterValue` for secrets | Create the secrets scope first: `databricks secrets create-scope <scope-name>`. |

### Missing resources after deploy

| Symptom | Fix |
|---|---|
| Schemas not found | Run the `setup_infrastructure` job -- it creates the Lakebase instance and tables. Schemas may also need manual creation via SQL if not included in the setup notebooks. |
| Volumes not found | Create them manually: `CREATE VOLUME IF NOT EXISTS main.bronze_tesla_lease_tracker.metadata;` and similar for `artifacts`. |
| SQL Warehouse not starting | Check the warehouse in the Databricks UI. Free tier may have a single warehouse limit. Stop other warehouses first. |
| Delta table missing | Re-run the `setup_infrastructure` job, or execute `notebooks/setup/2_create_delta_table.sql` manually in a SQL editor. |

### Bundle deploy failures

| Symptom | Fix |
|---|---|
| `YAML parse error` | Run `uv run python scripts/validate_dab_config.py --skip-workspace` to check for syntax issues. |
| `Resource already exists` | This is safe to ignore on re-deploy. DAB handles idempotent updates. |
| `bundle deploy` hangs | Check network connectivity to the workspace. Try `databricks workspace list /` to verify basic access. |
| Placeholder values still present | Run `uv run python scripts/validate_dab_config.py` -- it flags all `REPLACE_WITH_*` values. |

### App runtime errors

| Symptom | Fix |
|---|---|
| App returns 500 on `/api/health` | Check app logs: `databricks apps get-logs tesla-lease-tracker`. Verify environment variables are set. |
| Database connection refused | Ensure the Lakebase instance is running. Check `storage_mode` in config matches the deployed backend. |
| Tesla API auth failures | Verify OAuth tokens are fresh. Run `uv run python scripts/refresh_tesla_token.py` to renew. |
