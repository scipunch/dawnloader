DOCKER_IMAGE = scipunch-assistant

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

docker-build: lint
	docker build . -t $(DOCKER_IMAGE)

docker-run: docker-build
	docker run -d -e BOT_TOKEN=$$BOT_TOKEN $(DOCKER_IMAGE)

generate-requirements:
	uv export --no-hashes --format requirements-txt > requirements.txt
