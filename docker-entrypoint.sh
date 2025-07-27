#!/bin/bash
set -e

echo "Entrypoint script begin."

#start cron in the background
service cron start

echo "Entrypoint script complete!"

exec "$@"
