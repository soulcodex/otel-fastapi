# Show a list of available commands
help:
    just --list

# Generate the talk slides from Markdown
generate_slides:
    marp --input-dir ./.etc/slides --pdf --allow-local-files

# Watch for changes and regenerate slides automatically
watch_slides:
    marp --input-dir ./.etc/slides --pdf --watch --allow-local-files

# Run FastAPI example application
run-fast-api:
    [ -f ".env" ] || cp .env.example .env
    uv run python3 main.py

# Send sleep request to FastAPI example application
sleep-fast-api time_seconds="5":
    @curl -X POST "http://localhost:8000/sleep" -H "accept: application/json" -H "Content-Type: application/json" -d "{\"sleep_time_seconds\":{{ time_seconds }}}"
    echo "\n✅ Sleep request sent."

# Setup and run docker compose stack
up:
    docker-compose -f .docker/docker-compose.yaml up -d --build --force-recreate --remove-orphans

# Shutdown docker compose stack
down:
    docker-compose -f .docker/docker-compose.yaml down --remove-orphans --volumes
