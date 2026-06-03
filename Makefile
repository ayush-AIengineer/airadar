# AIRadar developer commands. Requires `uv` (https://docs.astral.sh/uv/).
# On Windows without `make`, run the `uv ...` command shown under each target directly.

.PHONY: install sync migrate makemigration downgrade pipeline-once seed test lint typecheck fmt clean

install: ## Pin Python 3.12 and install all dependency groups
	uv python pin 3.12
	uv sync --all-groups

sync: ## Install/refresh the base + dev environment
	uv sync

migrate: ## Apply all Alembic migrations to the configured DB
	uv run alembic upgrade head

makemigration: ## Autogenerate a migration: make makemigration m="add foo"
	uv run alembic revision --autogenerate -m "$(m)"

downgrade: ## Roll back the last migration
	uv run alembic downgrade -1

pipeline-once: ## Run the pipeline once for one source: make pipeline-once SOURCE=hackernews
	uv run airadar pipeline-once --source $(SOURCE)

seed: ## Load the source registry into the DB
	uv run airadar seed-sources

test: ## Run the test suite (no live network — VCR cassettes)
	uv run pytest

lint: ## Lint with ruff
	uv run ruff check .

fmt: ## Format with ruff
	uv run ruff format .

typecheck: ## Type-check with mypy
	uv run mypy airadar

clean: ## Remove caches and the local SQLite DB
	uv run python -c "import shutil,glob,os; [shutil.rmtree(p,ignore_errors=True) for p in glob.glob('**/__pycache__',recursive=True)]"
