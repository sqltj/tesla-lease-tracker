# Product Requirements Document: Tesla Lease Mileage Tracker

## 1. Overview

### Problem
Tesla lessees risk overage fees if they exceed their mileage allowance but have no simple way to track real odometer readings against their lease budget over time. Manually checking the Tesla app and doing mental math doesn't reveal trends, and by the time you realize you're over pace, it may be too late to adjust driving habits.

### Solution
A single-page web app that connects to the Tesla Fleet API, pulls real odometer readings on demand, tracks historical mileage against the lease allowance, and forecasts whether the driver will finish over or under their limit. Deployed as a Databricks App for authenticated access.

### Target User
An individual Tesla lessee who wants to monitor their lease mileage. Single-user, single-vehicle scope.

## 2. Goals and Non-Goals

### Goals
- Let users configure their lease terms (VIN, dates, mileage limit, start odometer)
- Pull live odometer data from the Tesla Fleet API with a single button click
- Display key metrics: miles used, daily average vs. budget rate, days remaining, projected overage/underage
- Visualize historical mileage and forecasted trajectory on a time-series chart
- Provide two forecasting models (linear regression and Holt-Winters exponential smoothing)
- Persist data across sessions without requiring a database

### Non-Goals
- Multi-user or multi-vehicle support
- Automatic/scheduled sync (vehicle wake concerns make on-demand sync intentional)
- Mobile-native app (responsive web only)
- Notifications or alerts
- Trip-level breakdown or driving analytics
- Lease payment or financial calculations

## 3. User Flows

### 3.1 First-Time Setup

1. User opens the app and sees a centered welcome screen with "Get Started" CTA
2. Clicking opens the Lease Configuration dialog
3. User enters:
   - **VIN** — their Tesla's 17-character vehicle identification number
   - **Lease Start Date** — when the lease began
   - **Lease End Date** — when the lease ends
   - **Mileage Limit** — total allowed miles over the lease term (e.g., 36,000)
   - **Start Odometer** — odometer reading at lease start
4. On save, the dashboard loads (initially empty, prompting a mileage sync)

### 3.2 Syncing Mileage

1. User clicks "Sync Mileage" button in the dashboard header
2. A warning toast appears: "This will wake your vehicle." with a "Sync anyway" action button
3. If confirmed, the app calls the Tesla Fleet API to fetch the current odometer
4. On success: reading is saved, dashboard and chart update, success toast shown
5. On failure: error toast with message (e.g., API timeout, auth expired)

### 3.3 Viewing the Dashboard

After at least one sync, the dashboard shows:

**Metrics Cards** (4-card grid):
| Card | Value | Subtext | Color Coding |
|------|-------|---------|--------------|
| Lease Miles Used | miles driven since lease start | "of X mi limit" | — |
| Daily Average | current mi/day rate | "budget: Y mi/day" | Red if over budget rate, green if under |
| Days Remaining | days until lease end | "of Z total" | — |
| Projected End | projected overage/underage in miles | "over/under limit (X mi projected)" | Red if over, green if under |

**Mileage Chart** (ComposedChart):
- Solid line: actual historical mileage readings
- Dashed line: forecasted future mileage
- Shaded area: confidence interval (time-series model only)
- Horizontal dashed red line: mileage limit
- Vertical dashed line: today marker
- X-axis: dates (MMM 'YY format), Y-axis: miles (in thousands)

**Forecast Toggle** (appears when 3+ readings exist):
- Toggle between "Linear" and "Time Series" forecast models
- Chart and forecast data update on toggle

### 3.4 Editing Lease Configuration

1. User clicks "Edit Lease" button in the dashboard header
2. Lease Configuration dialog opens pre-filled with current values
3. User modifies fields and saves
4. Dashboard recalculates all metrics

## 4. Data Model

### LeaseConfig (persisted)
| Field | Type | Description |
|-------|------|-------------|
| vin | string | Tesla VIN |
| lease_start_date | date | Lease start |
| lease_end_date | date | Lease end |
| mileage_limit | integer | Total allowed miles |
| start_odometer | float | Odometer at lease start |
| created_at | datetime | When config was created |
| updated_at | datetime | Last modification time |

### MileageReading (persisted)
| Field | Type | Description |
|-------|------|-------------|
| timestamp | datetime | When the reading was taken |
| odometer | float | Raw odometer value in miles |

### DashboardOut (computed)
| Field | Type | Description |
|-------|------|-------------|
| lease_miles_used | float | Current odometer minus start odometer |
| mileage_limit | integer | From lease config |
| daily_average | float | Lease miles used / days elapsed |
| budget_daily_rate | float | Mileage limit / total lease days |
| days_remaining | integer | Days until lease end |
| total_lease_days | integer | Full lease duration |
| projected_end_miles | float | daily_average * total_lease_days |
| over_under | float | projected_end_miles - mileage_limit |
| last_sync | datetime? | Timestamp of most recent sync |
| last_odometer | float? | Most recent odometer reading |

### ForecastOut (computed)
| Field | Type | Description |
|-------|------|-------------|
| model | string | "linear" or "prophet" |
| points | ForecastPoint[] | Series of date/predicted_miles/bounds |
| daily_rate | float | Predicted average mi/day |
| projected_end_miles | float | Predicted total lease miles at end |
| over_under | float | Positive = over limit |

## 5. API Endpoints

| Method | Path | Operation ID | Description |
|--------|------|-------------|-------------|
| GET | /api/lease | getLease | Returns lease config or null |
| PUT | /api/lease | saveLease | Create or update lease config |
| GET | /api/mileage | getMileage | List all readings with computed lease_miles |
| POST | /api/mileage/sync | syncMileage | Fetch odometer from Tesla API, store reading |
| GET | /api/dashboard | getDashboard | Computed metrics summary or null |
| GET | /api/forecast?model= | getForecast | Forecast (requires 3+ readings) |
| GET | /api/version | version | App version from package metadata |
| GET | /api/current-user | currentUser | Current Databricks user (OBO auth) |

## 6. Forecasting Models

### Linear Regression
- Fits a degree-1 polynomial (numpy polyfit) to historical readings
- Produces weekly forecast points from today through lease end + 30 days
- No confidence intervals
- Works well with consistent driving patterns

### Time Series (Holt-Winters)
- Uses statsmodels ExponentialSmoothing with additive trend, no seasonality
- Produces forecast points at intervals matching the average reading frequency
- Includes 95% confidence intervals (1.96 * std_err * sqrt(step))
- Falls back to linear regression if the model fails to converge
- Better captures trend changes in driving behavior

Both models require a minimum of 3 readings.

## 7. Architecture

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Persistence**: JSON file (`data/app_data.json`) — no database
- **Tesla Integration**: Direct Tesla Fleet API calls via aiohttp, OAuth refresh token flow, token caching, exponential backoff on 429s
- **Secret Management**: Databricks secret scopes (not environment variables)
- **Auth**: Databricks workspace identity via WorkspaceClient (service principal in prod, CLI profile in dev)

### Frontend
- **Framework**: React 19 + TypeScript + Vite
- **Routing**: TanStack Router (file-based, single route)
- **Data Fetching**: TanStack React Query with Suspense hooks
- **UI**: shadcn/ui components, Tailwind CSS
- **Charts**: Recharts (ComposedChart)
- **API Client**: Auto-generated TypeScript client from OpenAPI schema

### Deployment
- Databricks Apps via `databricks bundle deploy`
- Runs as `uvicorn` with 2 workers
- Backend serves static frontend assets at `/`, API at `/api`

## 8. Constraints and Assumptions

- **Single vehicle**: One lease config, one VIN. No multi-car support.
- **On-demand sync only**: Syncing wakes the Tesla from sleep, consuming battery. Users must explicitly trigger sync. No background polling.
- **Refresh token rotation**: Tesla refresh tokens expire after 90 days. The user must manually update the Databricks secret when this happens. The app surfaces the error clearly.
- **Minimum readings for forecast**: 3 odometer readings required before forecast features activate.
- **No offline mode**: Requires network access to both the Databricks workspace (for secrets) and Tesla Fleet API (for odometer).
- **JSON persistence**: Data is stored in a single JSON file. Suitable for single-user, low-volume data. Not designed for concurrent writes.

## 9. Future Considerations

### P1 — Pre-merge
- Error boundaries around all API-driven components
- Input validation (VIN format, date ordering, positive numbers)
- `.env.example` documenting required secrets

### P2 — Quality
- Backend unit tests (forecast edge cases, model serialization, persistence round-trip)
- Frontend component tests
- Success toasts on lease save, retry UI on sync failure

### P3 — Production polish
- Structured request logging with correlation IDs
- `/api/health` endpoint for deployment monitoring
- Rate limit visibility (show remaining Tesla API quota)
