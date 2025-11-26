#!/bin/bash

echo "Running DB initialization logic..."
python -m app.extract_from_eml
echo "DB initialization done."

echo "Starting Uvicorn..."
exec "$@"
