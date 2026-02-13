# Tesla Lease Mileage Tracker

Track your Tesla's odometer against your lease mileage allowance. Syncs real readings from the Tesla Fleet API, charts historical usage, and forecasts whether you'll be over or under your limit at lease end.

Built with [APX](https://github.com/databricks-solutions/apx) (FastAPI + React) and deployed as a Databricks App.

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **[Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/install.html)** — for deployment and secret management
- A **Databricks workspace** with a configured CLI profile
- A **Tesla Developer account** with OAuth credentials ([developer.tesla.com](https://developer.tesla.com))

## Local Development

### 1. Install dependencies

```bash
uv sync
```

This installs all Python dependencies (FastAPI, Pydantic, statsmodels, etc.) and the APX dev toolkit.

### 2. Configure Databricks authentication

The app uses the Databricks SDK to fetch Tesla secrets at runtime. Set up a CLI profile if you haven't already:

```bash
databricks configure --profile <your-profile>
```

Then export the profile so the SDK picks it up:

```bash
export DATABRICKS_CONFIG_PROFILE=<your-profile>
```

### 3. Set up Tesla API secrets

The app reads Tesla OAuth credentials from a Databricks secret scope. Create the scope and add your secrets:

```bash
databricks secrets create-scope tesla-lease-tracker
databricks secrets put-secret tesla-lease-tracker tesla-client-id
databricks secrets put-secret tesla-lease-tracker tesla-client-secret
databricks secrets put-secret tesla-lease-tracker tesla-refresh-token
```

Each command will prompt you for the secret value.

| Secret Key | Description |
|---|---|
| `tesla-client-id` | OAuth client ID from developer.tesla.com |
| `tesla-client-secret` | OAuth client secret from developer.tesla.com |
| `tesla-refresh-token` | Refresh token obtained via Tesla OAuth flow (expires every 90 days) |

### 4. Start the dev server

```bash
uv run apx dev start
```

This starts the backend (FastAPI), frontend (Vite), and OpenAPI client watcher. Open [http://127.0.0.1:9000](http://127.0.0.1:9000) in your browser.

Useful commands during development:

```bash
uv run apx dev status        # Check running servers
uv run apx dev logs -f       # Stream logs
uv run apx dev check         # Type-check TypeScript & Python
uv run apx dev stop          # Stop all servers
```

### Optional: environment overrides

The backend config can be overridden via a `.env` file at the project root or environment variables prefixed with `TESLA_LEASE_TRACKER_`:

| Variable | Default | Description |
|---|---|---|
| `TESLA_LEASE_TRACKER_TESLA_SECRET_SCOPE` | `tesla-lease-tracker` | Databricks secret scope name |
| `TESLA_LEASE_TRACKER_TESLA_API_REGION` | `na` | Tesla Fleet API region (`na`, `eu`, `cn`) |
| `TESLA_LEASE_TRACKER_DATA_FILE_PATH` | `data/app_data.json` | Path for JSON data persistence |

## Deploy to Databricks

### 1. Build

```bash
uv run apx build
```

This compiles the React frontend into static assets and packages everything into a Python wheel.

### 2. Deploy

```bash
databricks bundle deploy -p <your-profile>
```

This uploads the built artifacts and creates (or updates) the Databricks App resource defined in `databricks.yml`.

The deployed app runs via:
```
uvicorn tesla_lease_tracker.backend.app:app --workers 2
```

### Updating after changes

```bash
uv run apx build && databricks bundle deploy -p <your-profile>
```

## Project Structure

```
src/tesla_lease_tracker/
├── backend/
│   ├── app.py               # FastAPI entrypoint
│   ├── router.py             # API routes (/api/lease, /api/mileage, /api/dashboard, /api/forecast)
│   ├── models.py             # Pydantic data models
│   ├── data_store.py         # JSON file persistence
│   ├── tesla_service.py      # Tesla Fleet API client + OAuth
│   ├── forecast.py           # Linear regression + Holt-Winters forecasting
│   ├── config.py             # App settings (env vars + Databricks secrets)
│   ├── dependencies.py       # FastAPI dependency injection
│   ├── runtime.py            # Runtime initialization (WorkspaceClient, DataStore)
│   └── logger.py             # Logging configuration
└── ui/
    ├── routes/index.tsx       # Dashboard page route
    └── components/
        ├── dashboard/         # Metrics cards, mileage chart, sync button, forecast toggle
        └── lease/             # Lease configuration dialog
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Frontend | React 19, TypeScript, Vite |
| Routing | TanStack Router |
| Data Fetching | TanStack React Query |
| Charts | Recharts |
| UI Components | shadcn/ui, Tailwind CSS |
| Persistence | JSON file (no database) |
| Deployment | Databricks Apps |
