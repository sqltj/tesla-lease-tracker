# Tesla Lease Mileage Tracker

Track your Tesla's odometer against your lease mileage allowance. Syncs real readings from the Tesla Fleet API, charts historical usage, and forecasts whether you'll be over or under your limit at lease end.

Built with [APX](https://github.com/databricks-solutions/apx) (FastAPI + React) and deployed as a Databricks App.

## Getting Started

### Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **[Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/install.html)** — for deployment and secret management
- A **Databricks workspace** with a configured CLI profile

### Quick Start (exploring the UI locally)

Perfect for trying out the dashboard without Tesla API credentials:

1. **Install dependencies**
   ```bash
   uv sync
   ```

2. **Configure Databricks CLI**
   ```bash
   databricks configure --profile <your-profile>
   ```

   Optionally export the profile so the SDK picks it up:
   ```bash
   export DATABRICKS_CONFIG_PROFILE=<your-profile>
   ```

3. **Start the dev server**
   ```bash
   uv run apx dev start
   ```

   This starts the backend (FastAPI), frontend (Vite), and OpenAPI watcher. The dev server automatically provisions a local PGlite database — no external database setup needed.

4. **Seed sample data (optional)**

   ```bash
   uv run python scripts/seed_local.py
   ```

   This populates the database with realistic sample data: a 3-year Tesla Model Y lease with 19 mileage readings spanning 18 months. You'll see the dashboard at ~50% mileage usage (18,000 of 36,000 miles used).

   To reset and re-seed:
   ```bash
   uv run python scripts/seed_local.py --force
   ```

5. **Explore the UI**

   Open [http://127.0.0.1:9000](http://127.0.0.1:9000)

   If you seeded data, you'll see a fully populated dashboard with the hero gauge, metrics, and chart. If you didn't seed, use the lease configuration dialog to manually set up a sample lease, then explore the UI components. Without Tesla API credentials, you can test the frontend but won't be able to sync real mileage data.

#### Detailed Walkthrough

**Option A: With Sample Data (Recommended)**

1. **Seed the database**
   ```bash
   uv run python scripts/seed_local.py
   ```
   This inserts a 3-year Tesla Model Y lease (36k mile limit) with 19 historical readings.

2. **Open the dashboard** — http://127.0.0.1:9000

   You'll see:
   - Hero gauge at **50% usage** (~18,000 of 36,000 miles used)
   - Metrics cards populated (Daily Average: ~29 mi/day, Budget Rate: ~32.8 mi/day, etc.)
   - Chart displaying 19 data points with trend line
   - Working forecast toggle (Linear and Time Series models)

**Option B: Manual Configuration**

Once the dev server is running and you open http://127.0.0.1:9000:

1. **Empty dashboard** — You'll see:
   - Hero gauge at 0%
   - Empty metrics cards (Daily Average, Budget Rate, Days Remaining, Projected End)
   - Empty mileage chart
   - Disabled "Sync Mileage" button

2. **Configure a lease** — Click the **"⚙️ Configure Lease"** button and enter:
   - **VIN**: `5YJ3E1EA1NF123456` (or any valid 17-character VIN)
   - **Lease Start**: Any past date (e.g., `2024-06-01`)
   - **Lease End**: A future date (e.g., `2027-05-31`)
   - **Mileage Limit**: `36000` (or any limit)
   - **Starting Odometer**: `12.0` (starting miles on the car)
   - Click **Save**

3. **Dashboard updates** — After saving:
   - Hero gauge now shows **0% usage** (no readings yet)
   - Metrics cards show **0 mi/day** and **N/A** (waiting for data)
   - Chart remains empty (needs readings to display)
   - "Sync Mileage" button is now **enabled** (but won't work without Tesla API)

4. **Test the forecast toggle** — Click the toggle between "Linear" and "Time Series"
   - Toggles work but show no data (forecast needs at least 3 readings)

5. **Explore components** — You can now test:
   - Lease configuration updates (edit and save again)
   - UI responsiveness and styling
   - Error handling (try invalid VIN, reversed dates, etc.)

**Useful commands during development:**

```bash
uv run apx dev status        # Check running servers
uv run apx dev logs -f       # Stream logs
uv run apx dev check         # Type-check TypeScript & Python
uv run apx dev stop          # Stop all servers
uv run pytest tests/backend/ -v  # Run backend tests (54 tests)
```

### Full Setup (with Tesla API credentials)

For syncing real odometer readings from your Tesla:

1. **Follow steps 1-3 above** (install dependencies, configure Databricks, start dev server)

2. **Register with Tesla Fleet API** (one-time setup)

   This app requires Tesla Fleet API access. Follow these steps:

   **Step A: Generate Key Pair**
   ```bash
   # Generate private key
   openssl ecparam -name prime256v1 -genkey -noout -out private-key.pem

   # Extract public key
   openssl ec -in private-key.pem -pubout -out public-key.pem
   ```

   **Step B: Host Public Key**
   - Host `public-key.pem` at: `https://your-domain.com/.well-known/appspecific/com.tesla.3p.public-key.pem`
   - Tesla will verify this URL to confirm domain ownership

   **Step C: Deploy App & Get a Domain**

   The app must have a **publicly accessible URL** (domain) for Tesla to verify your public key location.

   **For Databricks deployment:**
   ```bash
   uv run apx build
   databricks bundle deploy -p <your-profile>
   ```
   This gives you a URL like: `https://dbc-xxxxxxxx.cloud.databricks.com/apps/tesla-lease-tracker`

   **For your own server/domain:** Use your domain URL (e.g., `tesla-lease-tracker.example.com`)

   **Step D: Register with Tesla**

   Use the automated registration script:
   ```bash
   uv run python scripts/register_fleet_api.py \
     --domain your-deployed-domain.com \
     --region na  # or 'eu', 'cn'
   ```

   The script will:
   - Automatically get your partner token from Databricks secrets
   - Load your public key from `public-key.pem`
   - Call Tesla's register endpoint
   - Show you the status

   **Alternatively, manually register** (if not using Databricks):
   ```bash
   uv run python scripts/register_fleet_api.py \
     --domain your-domain.com \
     --region na \
     --client-id YOUR_CLIENT_ID \
     --client-secret YOUR_CLIENT_SECRET
   ```

   Note: Registration approval can take 1-24 hours. You'll receive a confirmation email.

3. **Get Tesla OAuth credentials** from [developer.tesla.com](https://developer.tesla.com)

   When creating your OAuth application:
   - Set redirect URI to: `http://localhost:8080/callback`
   - Enable these scopes:
     - `openid`
     - `email`
     - `offline_access`
     - `vehicle_device_data` (required for Fleet API)

3. **Get your refresh token**

   Run the automated OAuth script:
   ```bash
   uv run python scripts/get_tesla_refresh_token_auto.py \
     --client-id YOUR_CLIENT_ID \
     --client-secret YOUR_CLIENT_SECRET
   ```

   This will:
   - Open Tesla authorization page in your browser
   - Start a local server to capture the callback
   - Exchange the authorization code for a refresh token
   - Display your refresh token to copy

4. **Create secret scope and add credentials**
   ```bash
   databricks secrets create-scope tesla-lease-tracker
   databricks secrets put-secret tesla-lease-tracker tesla-client-id --string-value "YOUR_CLIENT_ID"
   databricks secrets put-secret tesla-lease-tracker tesla-client-secret --string-value "YOUR_CLIENT_SECRET"
   databricks secrets put-secret tesla-lease-tracker tesla-refresh-token --string-value "YOUR_REFRESH_TOKEN"
   ```

   | Secret Key | Description |
   |---|---|
   | `tesla-client-id` | OAuth client ID from developer.tesla.com |
   | `tesla-client-secret` | OAuth client secret from developer.tesla.com |
   | `tesla-refresh-token` | Refresh token from OAuth flow (expires every 90 days) |

5. **Use the app**

   Open [http://127.0.0.1:9000](http://127.0.0.1:9000), configure your lease details, then click "Sync Mileage" to fetch real data from the Tesla Fleet API.

### Environment Variables

#### Local Development

APX auto-provisions PGlite and sets these automatically:
- `APX_DEV_DB_PORT` — Database port
- `APX_DEV_DB_PWD` — Database password

Optional overrides (create `.env` file or export):
- `TESLA_LEASE_TRACKER_STORAGE_MODE=json` — Use JSON instead of database
- `TESLA_LEASE_TRACKER_TESLA_SECRET_SCOPE=custom-scope` — Custom secret scope name
- `TESLA_LEASE_TRACKER_TESLA_API_REGION=na` — Tesla Fleet API region (`na`, `eu`, `cn`)
- `TESLA_LEASE_TRACKER_DATA_FILE_PATH=data/app_data.json` — JSON file path (only used when `storage_mode=json`)
- `DATABRICKS_CONFIG_PROFILE=<name>` — Use specific Databricks CLI profile

#### Databricks Deployment

Set in `databricks.yml` or workspace environment:
- `TESLA_LEASE_TRACKER_STORAGE_MODE=database` (default)
- `TESLA_LEASE_TRACKER_TESLA_SECRET_SCOPE=tesla-lease-tracker`
- `TESLA_LEASE_TRACKER_ZEROBUS_CATALOG=main`
- `TESLA_LEASE_TRACKER_ZEROBUS_SCHEMA=default`
- `PGAPPNAME=tesla-lease-tracker` — Lakebase instance name

## Deploy to Databricks

### Pre-Deployment Checklist

Before deploying, ensure you have:
- [ ] Configured Databricks CLI: `databricks auth login --host <workspace-url>`
- [ ] Created Tesla OAuth credentials at [developer.tesla.com](https://developer.tesla.com)
- [ ] Added Tesla credentials to Databricks secrets:
  ```bash
  databricks secrets create-scope tesla-lease-tracker
  databricks secrets put-secret tesla-lease-tracker tesla-client-id --string-value "YOUR_CLIENT_ID"
  databricks secrets put-secret tesla-lease-tracker tesla-client-secret --string-value "YOUR_CLIENT_SECRET"
  ```
- [ ] (Optional) Obtained Tesla refresh token:
  ```bash
  uv run python scripts/get_tesla_refresh_token_auto.py \
    --client-id YOUR_CLIENT_ID \
    --client-secret YOUR_CLIENT_SECRET
  ```
  Then store it in Databricks secrets.

### Deployment Steps

### 1. Provision Infrastructure

**Create a Lakebase instance** (managed PostgreSQL for transactional data):

```bash
databricks database create-database-instance \
    --name tesla-lease-tracker \
    --capacity SMALL \
    --profile <your-profile>
```

Wait for creation to complete (~5-10 minutes).

**Create the Zerobus Delta table** (for analytics streaming):

```bash
databricks sql execute "CREATE TABLE IF NOT EXISTS main.default.mileage_readings (
    vin STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    odometer DOUBLE NOT NULL
) USING DELTA;" \
    --profile <your-profile>
```

Or use the Databricks SQL editor to run the query manually.

### 2. Build

```bash
uv run apx build
```

This compiles the React frontend into static assets and packages everything into a Python wheel.

### 3. Deploy

```bash
databricks bundle deploy -p <your-profile>
```

This uploads the built artifacts and creates (or updates) the Databricks App resource defined in `databricks.yml`, including the Lakebase database resource.

The deployed app runs via:
```
uvicorn tesla_lease_tracker.backend.app:app --workers 2
```

### 4. Post-Deployment Setup

After deployment completes, run these steps to enable Tesla sync:

**Step A: Get your deployed URL**
```bash
databricks app get tesla-lease-tracker --profile <your-profile>
# Look for the "url" field in the output
# Example: https://dbc-xxxxxxxx.cloud.databricks.com/apps/tesla-lease-tracker
```

**Step B: Complete Tesla Fleet API Registration** (one-time setup)

Register your deployed domain with Tesla's Fleet API:
```bash
# Generate key pair first (if not already done)
openssl ecparam -name prime256v1 -genkey -noout -out private-key.pem
openssl ec -in private-key.pem -pubout -out public-key.pem

# Register with Tesla (uses secrets from Databricks)
uv run python scripts/register_fleet_api.py \
  --domain dbc-xxxxxxxx.cloud.databricks.com/apps/tesla-lease-tracker \
  --region na
```

The script will:
- Retrieve your Tesla OAuth credentials from Databricks secrets
- Get a partner authentication token
- Register your domain with Tesla's Fleet API
- Show you the status

**Step C: (Optional) Seed sample data**

To test the app with realistic sample lease data before syncing real Tesla data:
```bash
# This requires local dev tools, so you'd run this locally and then have
# data available when deployed (if using same database)
# Or use the UI to manually add a lease and readings
```

**Step D: Verify setup**

- Open your deployed URL: `https://dbc-xxxxxxxx.cloud.databricks.com/apps/tesla-lease-tracker`
- Configure a lease in the UI
- Wait for Tesla Fleet API registration approval (1-24 hours, you'll get an email)
- Once approved, the "Sync Mileage" button will work

### Migrating existing JSON data

If you have an existing JSON data file and are switching to database storage:

```bash
uv run python scripts/migrate_json_to_lakebase.py --json-path data/app_data.json
```

### Updating after changes

```bash
uv run apx build && databricks bundle deploy -p <your-profile>
```

## Project Structure

```
src/tesla_lease_tracker/
├── backend/
│   ├── app.py               # FastAPI entrypoint + lifespan (DB/Zerobus init)
│   ├── router.py             # API routes (/api/lease, /api/mileage, /api/dashboard, /api/forecast)
│   ├── models.py             # Pydantic API models (request/response contracts)
│   ├── db_models.py          # SQLModel table definitions (LeaseConfigDB, MileageReadingDB, AppStateDB)
│   ├── repositories.py       # Repository layer (LeaseRepository, MileageRepository)
│   ├── data_store.py         # JSON file persistence (fallback)
│   ├── tesla_service.py      # Tesla Fleet API client + OAuth
│   ├── zerobus_service.py    # Zerobus Ingest SDK wrapper (Delta table streaming)
│   ├── forecast.py           # Linear regression + Holt-Winters forecasting
│   ├── config.py             # App settings (DatabaseConfig, Zerobus config, storage_mode)
│   ├── dependencies.py       # FastAPI dependency injection (repos, sessions, config)
│   ├── runtime.py            # Runtime initialization (SQLAlchemy engine, WorkspaceClient)
│   └── logger.py             # Structured JSON logging
└── ui/
    ├── routes/index.tsx       # Dashboard page route
    └── components/
        ├── dashboard/         # Metrics cards, mileage chart, sync button, forecast toggle
        └── lease/             # Lease configuration dialog
```

## Storage Architecture

The app uses a **dual-storage architecture** with a JSON file fallback:

### Database mode (default)

**Lakebase Provisioned** (managed PostgreSQL) stores transactional data with ACID guarantees:

| Table | Contents |
|---|---|
| `lease_config` | VIN, lease dates, mileage limit, start odometer, timestamps |
| `mileage_readings` | Timestamped odometer readings per VIN |
| `app_state` | Last sync timestamp |

**Zerobus Ingest** additionally streams each mileage reading to a Delta table (`{catalog}.{schema}.mileage_readings`) for analytics workloads. This is non-fatal — if Zerobus is unavailable, data is still written to Lakebase.

In local development, `apx dev start` automatically provisions a PGlite instance (embedded PostgreSQL) — no external database setup required.

### JSON mode (fallback)

Set `TESLA_LEASE_TRACKER_STORAGE_MODE=json` to use flat-file persistence. All state is stored in a single JSON file (`data/app_data.json` by default):

```json
{
  "lease_config": {
    "vin": "5YJ3E1EA1PF...",
    "lease_start_date": "2024-01-15",
    "lease_end_date": "2027-01-15",
    "mileage_limit": 36000,
    "start_odometer": 12.0,
    "created_at": "...",
    "updated_at": "..."
  },
  "readings": [
    { "timestamp": "2024-02-01T12:00:00", "odometer": 1024.5 },
    { "timestamp": "2024-03-01T12:00:00", "odometer": 2150.3 }
  ],
  "last_sync": "2024-03-01T12:00:00"
}
```

### What's stored

- **Lease config** — User-provided lease terms (VIN, dates, mileage limit, starting odometer). Entered once via the lease setup form and updatable at any time.
- **Mileage readings** — Appended on each sync from the Tesla Fleet API. Each reading is a timestamped odometer value.
- **Last sync** — Timestamp of the most recent Tesla API sync.

Dashboard metrics (daily average, projected end miles, over/under budget) and forecasts (linear regression, Holt-Winters) are **computed on the fly** from the stored data — nothing else is persisted.

## Testing

```bash
uv run pytest tests/backend/ -v    # 54 backend tests (models, repos, forecast, middleware, Zerobus)
uv run apx bun run test            # 13 frontend tests (vitest)
uv run apx dev check               # TypeScript + Python type checks
```

## Troubleshooting

### Tesla OAuth / Refresh Token Issues

**Problem**: "We don't recognize this redirect_uri"
- **Solution**: Make sure your redirect URI in the Tesla developer app matches what you're using in the script. Default is `http://localhost:8080/callback`.

**Problem**: Refresh token expires every 90 days
- **Solution**: The app uses refresh tokens to get new access tokens automatically. If you see a "refresh token expired" error, you'll need to re-run the OAuth flow to get a new refresh token:
  ```bash
  uv run python scripts/get_tesla_refresh_token_auto.py --client-id YOUR_ID --client-secret YOUR_SECRET
  ```
  Then update the Databricks secret with the new token.

**Problem**: "vehicle_device_data" scope errors
- **Solution**: Make sure you've enabled the `vehicle_device_data` scope in your Tesla developer app — it's required for Fleet API access to odometer readings.

**Problem**: "Account must be registered in the current region" (412 error during sync)
- **Solution**: Your OAuth client ID must be registered with Tesla's Fleet API in the region you're trying to access.
  - Go to [Tesla Developer Console](https://developer.tesla.com)
  - Register your OAuth application in the appropriate region (the app uses `na` by default for North America)
  - Alternatively, change the region in `.env` or set `TESLA_LEASE_TRACKER_TESLA_API_REGION` environment variable to match where your account is registered (`eu`, `cn`, etc.)
  - Verify you're using the correct VIN for a vehicle associated with your Tesla account

### Local Development

**Empty dashboard?**
- Run the seed script to populate sample data: `uv run python scripts/seed_local.py`
- Or configure a lease manually and sync real data with valid Tesla credentials

**Dev server won't start?**
- Make sure no other process is using port 9000: `lsof -i :9000`
- Check APX status: `uv run apx dev status`

## Future Improvements

See [DEPLOYMENT_ROADMAP.md](./DEPLOYMENT_ROADMAP.md) for planned enhancements:
- **Automated Infrastructure Setup**: Move Lakebase + Delta table creation to DAB notebooks
- **Single-Command Post-Deploy**: `uv run python scripts/post_deploy_setup.py` to complete all setup
- **Multi-Region Support**: Simplified regional deployment
- **Monitoring & Alerting**: Built-in dashboards for mileage data quality

These improvements will make Databricks deployment even more streamlined.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Database | Lakebase Provisioned (managed PostgreSQL) via SQLModel |
| Streaming | Zerobus Ingest (Delta table) |
| Frontend | React 19, TypeScript, Vite |
| Routing | TanStack Router |
| Data Fetching | TanStack React Query |
| Charts | Recharts |
| UI Components | shadcn/ui, Tailwind CSS |
| Deployment | Databricks Apps |
