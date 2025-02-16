format:
	uv run ruff format

lint: format
	uv run ruff check --fix
	uv run codespell .
	uv run mypy .

# Run fast and free tests
test: lint
	uv run pytest -m "not paid"

pre-commit: lint

run: lint
	uv run python __main__.py

generate-requirements:
	uv export --no-hashes --format requirements-txt > requirements.txt
