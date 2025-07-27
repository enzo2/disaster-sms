# Install uv
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies before copying the project files
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

FROM python:3.13-slim

# copy the installed project from the builder stage
COPY --from=builder /app /app
WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    cron \
    procps \
    nano

# Make the entrypoint script executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Establish the cron jobs file
COPY crontab /etc/cron.d/cron_jobs
RUN chown root:root /etc/cron.d/cron_jobs
RUN chmod 0644 /etc/cron.d/cron_jobs

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=2 \
  CMD curl --fail http://localhost:8080/health || exit 1

# Set the entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Expose the flask app port
EXPOSE 8080

# Run the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]