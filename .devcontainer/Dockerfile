FROM mcr.microsoft.com/devcontainers/python:3.13

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    cron \
    procps \
    nano

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . .

# Install Python dependencies using uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked

# Make the entrypoint script executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Establish the cron jobs file
COPY crontab /etc/cron.d/cron_jobs
RUN chown root:root /etc/cron.d/cron_jobs
RUN chmod 0644 /etc/cron.d/cron_jobs

# Set the entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Expose the flask app port
EXPOSE 8080

# Run the Flask app
#CMD ["python", "app.py"]
