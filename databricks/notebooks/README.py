# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # Tesla Lease Tracker
# MAGIC
# MAGIC Track your Tesla's odometer against your lease mileage allowance.
# MAGIC
# MAGIC **Sync real readings** from the Tesla Fleet API → **Chart historical usage** → **Forecast** whether you'll be over or under your limit at lease end.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🏗️ Architecture
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────┐
# MAGIC │                    Deployed Databricks App                  │
# MAGIC ├─────────────────────────────────────────────────────────────┤
# MAGIC │                                                             │
# MAGIC │  ┌──────────────┐              ┌──────────────────────┐   │
# MAGIC │  │   Frontend   │              │   Backend (FastAPI)  │   │
# MAGIC │  │  (React 19)  │◄────────────►│   (Python)           │   │
# MAGIC │  │              │              │                      │   │
# MAGIC │  │ • Dashboard  │              │ • API routes         │   │
# MAGIC │  │ • Charts     │              │ • Forecasting        │   │
# MAGIC │  │ • Lease Form │              │ • Tesla integration  │   │
# MAGIC │  └──────────────┘              └──────────────────────┘   │
# MAGIC │                                         ▲                  │
# MAGIC │                                         │                  │
# MAGIC │                    ┌────────────────────┼────────────────┐ │
# MAGIC │                    │                    │                │ │
# MAGIC │              ┌─────▼─────┐      ┌──────▼────────┐   ┌──┴─▼──┐
# MAGIC │              │  Lakebase  │      │   Zerobus     │   │ Tesla │
# MAGIC │              │ (Database) │      │ (Analytics)   │   │ Fleet │
# MAGIC │              │            │      │   Delta table │   │  API  │
# MAGIC │              │ • Leases   │      │               │   │       │
# MAGIC │              │ • Readings │      │ • Streaming   │   │       │
# MAGIC │              │ • State    │      │   mileage     │   │       │
# MAGIC │              └────────────┘      └───────────────┘   └───────┘
# MAGIC │
# MAGIC └─────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC **Data Flow:**
# MAGIC 1. User clicks "Sync Mileage" in dashboard
# MAGIC 2. Backend fetches current odometer from Tesla Fleet API
# MAGIC 3. Reading stored in Lakebase + streamed to Zerobus Delta table
# MAGIC 4. Frontend displays updated dashboard with historical trend & forecast

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📁 Project Structure
# MAGIC
# MAGIC ```
# MAGIC tesla-lease-tracker/
# MAGIC ├── src/tesla_lease_tracker/
# MAGIC │   ├── ui/                          # React frontend
# MAGIC │   │   ├── components/dashboard/    # Dashboard UI
# MAGIC │   │   ├── routes/                  # TanStack Router pages
# MAGIC │   │   └── lib/api.ts               # Auto-generated OpenAPI client
# MAGIC │   │
# MAGIC │   └── backend/                     # FastAPI backend
# MAGIC │       ├── router.py                # API endpoints
# MAGIC │       ├── tesla_service.py         # Tesla Fleet API client
# MAGIC │       ├── repositories.py          # Database layer
# MAGIC │       ├── forecast.py              # Forecasting algorithms
# MAGIC │       └── app.py                   # FastAPI entrypoint
# MAGIC │
# MAGIC ├── scripts/
# MAGIC │   ├── register_fleet_api.py        # Register with Tesla (post-deploy)
# MAGIC │   ├── get_tesla_refresh_token_auto.py
# MAGIC │   ├── seed_local.py                # Sample data for local dev
# MAGIC │   └── post_deploy_setup.py         # Post-deployment automation (planned)
# MAGIC │
# MAGIC ├── databricks/notebooks/            # Deployed to /Users/{email}/tesla-lease-tracker/notebooks
# MAGIC │   ├── setup/
# MAGIC │   │   ├── 1_create_lakebase.py    # Provision database
# MAGIC │   │   └── 2_create_delta_table.sql # Create analytics table
# MAGIC │   └── README.py                    # This notebook
# MAGIC │
# MAGIC ├── tests/
# MAGIC │   ├── backend/                     # 54 pytest tests
# MAGIC │   └── frontend/                    # 13 vitest tests
# MAGIC │
# MAGIC ├── databricks.yml                   # Deployment configuration
# MAGIC ├── pyproject.toml                   # Python dependencies
# MAGIC └── README.md                        # Full documentation
# MAGIC ```
# MAGIC
# MAGIC **Note on Workspace Deployment:**
# MAGIC When deployed to Databricks, notebooks are organized under your user workspace at:
# MAGIC - `/Users/{your_email}/tesla-lease-tracker/notebooks/README.py`
# MAGIC - `/Users/{your_email}/tesla-lease-tracker/notebooks/setup/1_create_lakebase.py`
# MAGIC - `/Users/{your_email}/tesla-lease-tracker/notebooks/setup/2_create_delta_table.sql`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚀 Quick Start
# MAGIC
# MAGIC ### Local Development
# MAGIC
# MAGIC ```bash
# MAGIC # 1. Install dependencies
# MAGIC uv sync
# MAGIC
# MAGIC # 2. Start dev servers (backend, frontend, OpenAPI watcher)
# MAGIC uv run apx dev start
# MAGIC # Open http://127.0.0.1:9000
# MAGIC
# MAGIC # 3. (Optional) Seed sample data to see populated dashboard
# MAGIC uv run python scripts/seed_local.py
# MAGIC ```
# MAGIC
# MAGIC ### Databricks Deployment
# MAGIC
# MAGIC ```bash
# MAGIC # 1. Set up infrastructure
# MAGIC databricks database create-database-instance --name tesla-lease-tracker --capacity SMALL
# MAGIC
# MAGIC # 2. Build and deploy
# MAGIC uv run apx build
# MAGIC databricks bundle deploy -p <your-profile>
# MAGIC
# MAGIC # 3. Post-deployment setup
# MAGIC uv run python scripts/post_deploy_setup.py --profile <your-profile>
# MAGIC
# MAGIC # 4. Register with Tesla Fleet API
# MAGIC uv run python scripts/register_fleet_api.py --domain <your-deployed-domain>
# MAGIC
# MAGIC # 5. Wait for Fleet API approval (~1-24 hours)
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Key Features
# MAGIC
# MAGIC | Feature | Details |
# MAGIC |---------|---------|
# MAGIC | **Real-time Sync** | Fetch current odometer from Tesla Fleet API |
# MAGIC | **Historical Tracking** | 19+ readings shown in interactive chart |
# MAGIC | **Forecasting** | Predict if you'll exceed lease mileage limit using Linear or Holt-Winters models |
# MAGIC | **Responsive Dashboard** | Glass-morphism design, real-time updates, metric cards |
# MAGIC | **Structured Logging** | JSON logs with correlation IDs for debugging |
# MAGIC | **Dual Storage** | Lakebase PostgreSQL (primary) + JSON fallback |
# MAGIC | **Analytics Streaming** | Zerobus non-fatal streaming to Delta table |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📊 Database Schema
# MAGIC
# MAGIC ### Lakebase Tables
# MAGIC
# MAGIC **lease_config** - User's lease terms
# MAGIC ```
# MAGIC vin              STRING       NOT NULL  # Vehicle ID
# MAGIC lease_start_date DATE         NOT NULL
# MAGIC lease_end_date   DATE         NOT NULL
# MAGIC mileage_limit    INT          NOT NULL
# MAGIC start_odometer   FLOAT        NOT NULL
# MAGIC created_at       TIMESTAMP    NOT NULL
# MAGIC updated_at       TIMESTAMP    NOT NULL
# MAGIC ```
# MAGIC
# MAGIC **mileage_readings** - Historical odometer readings
# MAGIC ```
# MAGIC vin              STRING       NOT NULL
# MAGIC timestamp        TIMESTAMP    NOT NULL
# MAGIC odometer         FLOAT        NOT NULL
# MAGIC ```
# MAGIC
# MAGIC **app_state** - Last sync timestamp
# MAGIC ```
# MAGIC key              STRING       PRIMARY KEY
# MAGIC value            STRING
# MAGIC updated_at       TIMESTAMP
# MAGIC ```
# MAGIC
# MAGIC ### Zerobus Delta Table
# MAGIC
# MAGIC **main.default.mileage_readings** - Analytics table (non-fatal streaming)
# MAGIC ```
# MAGIC vin              STRING       NOT NULL
# MAGIC timestamp        TIMESTAMP    NOT NULL
# MAGIC odometer         DOUBLE       NOT NULL
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧪 Testing
# MAGIC
# MAGIC ```bash
# MAGIC # Backend tests (54 tests)
# MAGIC uv run pytest tests/backend/ -v
# MAGIC
# MAGIC # Frontend tests (13 tests)
# MAGIC uv run apx bun run test
# MAGIC
# MAGIC # Type checking
# MAGIC uv run apx dev check
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔐 Security & Secrets
# MAGIC
# MAGIC ### Databricks Secrets
# MAGIC
# MAGIC Store Tesla credentials in Databricks secrets scope `tesla-lease-tracker`:
# MAGIC
# MAGIC ```bash
# MAGIC databricks secrets create-scope tesla-lease-tracker
# MAGIC databricks secrets put-secret tesla-lease-tracker tesla-client-id --string-value "YOUR_ID"
# MAGIC databricks secrets put-secret tesla-lease-tracker tesla-client-secret --string-value "YOUR_SECRET"
# MAGIC databricks secrets put-secret tesla-lease-tracker tesla-refresh-token --string-value "YOUR_TOKEN"
# MAGIC ```
# MAGIC
# MAGIC ### No Secrets in Code
# MAGIC ✅ All credentials stored in Databricks secrets
# MAGIC ✅ No `.env` files committed to git
# MAGIC ✅ No hardcoded tokens anywhere
# MAGIC ✅ Keys rotated via scripts, not in source

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📚 Documentation
# MAGIC
# MAGIC - **[README.md](https://github.com/sqltj/tesla-lease-tracker)** - Full project documentation
# MAGIC - **[DEPLOYMENT_ROADMAP.md](https://github.com/sqltj/tesla-lease-tracker)** - Future infrastructure improvements
# MAGIC - **[CLAUDE.md](https://github.com/sqltj/tesla-lease-tracker)** - Development guidelines & conventions
# MAGIC
# MAGIC ### Key Docs
# MAGIC
# MAGIC | Topic | Location |
# MAGIC |-------|----------|
# MAGIC | Local Setup | README.md - Quick Start |
# MAGIC | Databricks Deployment | README.md - Deploy to Databricks |
# MAGIC | Tesla Fleet API Setup | README.md - Full Setup (with Tesla API credentials) |
# MAGIC | Troubleshooting | README.md - Troubleshooting |
# MAGIC | Architecture | README.md - Project Structure |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🛠️ Common Commands
# MAGIC
# MAGIC ### Development
# MAGIC ```bash
# MAGIC uv run apx dev start          # Start all dev servers
# MAGIC uv run apx dev check          # Type check TypeScript & Python
# MAGIC uv run apx dev logs -f        # Stream logs
# MAGIC uv run apx dev stop           # Stop servers
# MAGIC ```
# MAGIC
# MAGIC ### Deployment
# MAGIC ```bash
# MAGIC uv run apx build              # Build for production
# MAGIC databricks bundle deploy      # Deploy to Databricks
# MAGIC uv run python scripts/post_deploy_setup.py --profile <profile>
# MAGIC uv run python scripts/register_fleet_api.py --domain <domain>
# MAGIC ```
# MAGIC
# MAGIC ### Testing
# MAGIC ```bash
# MAGIC uv run pytest tests/backend/ -v
# MAGIC uv run apx bun run test
# MAGIC ```
# MAGIC
# MAGIC ### Local Data
# MAGIC ```bash
# MAGIC uv run python scripts/seed_local.py      # Add sample data
# MAGIC uv run python scripts/seed_local.py --force  # Reset and re-seed
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚡ Key Technologies
# MAGIC
# MAGIC | Layer | Tech Stack |
# MAGIC |-------|-----------|
# MAGIC | **Frontend** | React 19, TypeScript, Vite 7, TanStack Router, Recharts |
# MAGIC | **Backend** | FastAPI, Pydantic, SQLModel |
# MAGIC | **Database** | Lakebase Provisioned (managed PostgreSQL) + Zerobus |
# MAGIC | **Integration** | Tesla Fleet API, Databricks SDK |
# MAGIC | **UI Components** | shadcn/ui, Radix UI, Tailwind CSS |
# MAGIC | **Deployment** | Databricks Apps, APX Framework |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🚦 Troubleshooting
# MAGIC
# MAGIC ### 502 Bad Gateway on Sync
# MAGIC → Your OAuth account needs to be registered with Tesla Fleet API. See README - Troubleshooting section.
# MAGIC
# MAGIC ### Refresh Token Expired
# MAGIC → Refresh tokens expire every 90 days. Re-run the OAuth script:
# MAGIC ```bash
# MAGIC uv run python scripts/get_tesla_refresh_token_auto.py --client-id YOUR_ID --client-secret YOUR_SECRET
# MAGIC ```
# MAGIC
# MAGIC ### Dev Server Won't Start
# MAGIC → Check if port 9000 is in use: `lsof -i :9000`
# MAGIC → Or check APX status: `uv run apx dev status`
# MAGIC
# MAGIC ### Empty Dashboard
# MAGIC → Seed sample data: `uv run python scripts/seed_local.py`
# MAGIC → Or configure a lease manually in the UI and sync real data

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📞 Getting Help
# MAGIC
# MAGIC 1. **Check README.md** - Most common issues covered
# MAGIC 2. **Check logs** - `uv run apx dev logs -f` for detailed error messages
# MAGIC 3. **Check Databricks workspace** - Job logs for deployment issues
# MAGIC 4. **Check GitHub** - https://github.com/sqltj/tesla-lease-tracker

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📝 Development Notes
# MAGIC
# MAGIC - **Always branch** for new features - never commit directly to `main`
# MAGIC - **Run type checks** after changes: `uv run apx dev check`
# MAGIC - **Run tests** before creating PRs: `uv run pytest tests/backend/ && uv run apx bun run test`
# MAGIC - **Use error boundaries** on frontend (CLAUDE.md requirement)
# MAGIC - **MCP tools preferred** over CLI when available

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC **Questions?** Check the [GitHub repository](https://github.com/sqltj/tesla-lease-tracker) or review the [full README](./README.md).
# MAGIC
# MAGIC **Version:** 0.1.0 | **Last Updated:** 2026-02-14
