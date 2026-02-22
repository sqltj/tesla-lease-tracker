# Repository Guidelines

## Project Structure
- `src/tesla_lease_tracker/backend/` holds the FastAPI app, config, data access, and storage logic.
- `src/tesla_lease_tracker/ui/` contains the React + Vite frontend (`components/`, `routes/`, `types/`).
- `tests/backend/` is the Pytest suite for backend logic.
- `scripts/` includes local utilities such as `seed_local.py` for sample data.
- `data/` is used for JSON fallback storage in local development.
- `databricks/` plus `databricks.yml` define Databricks Asset Bundles for deployment.

## Build, Test, and Development Commands
- `uv sync` installs Python dependencies via `uv`.
- `uv run apx dev start` runs the FastAPI backend, Vite dev server, and OpenAPI watcher.
- `uv run apx dev check` runs Python and TypeScript type checks.
- `uv run python scripts/seed_local.py` seeds local sample data for the dashboard.
- `uv run pytest tests/backend/ -v` executes backend tests.
- `uv run apx bun run test` executes frontend Vitest tests.

## Coding Style & Naming Conventions
- Python uses 4-space indentation, `snake_case` for functions/vars, and `PascalCase` for classes.
- TypeScript/React uses 2-space indentation, `PascalCase` components, `camelCase` hooks, and `kebab-case.tsx` filenames (e.g., `dashboard-page.tsx`).
- Keep modules grouped by feature (e.g., `dashboard`, `lease`) and favor small, focused components.

## Testing Guidelines
- Backend tests live in `tests/backend/` and use `pytest` + `pytest-asyncio`; name files `test_*.py`.
- Frontend tests live beside components in `src/tesla_lease_tracker/ui/components/**/__tests__` and use `*.test.tsx`.
- Add or update tests when changing forecast logic, storage behavior, or UI flows.

## Commit & Pull Request Guidelines
- Commits use imperative, capitalized summaries (e.g., “Add Zerobus fallback”).
- PRs include a short summary, linked issues, and the exact test commands run.
- Include screenshots or a short recording for UI changes, plus any Tesla or Databricks setup needed to validate.

## Configuration & Secrets
- Local development relies on `DATABRICKS_CONFIG_PROFILE` and Tesla API credentials.
- Store secrets in Databricks or local env vars, and avoid committing `.env` files or tokens.
- Document new environment variables in `README.md` when introduced.
