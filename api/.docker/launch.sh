#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR" || exit

cp ../.env.srv ../.env
export APPLICATION_NAME="t-iot-902-api"
docker compose down --remove-orphans
docker compose up "$@" --detach
docker container exec -it "$APPLICATION_NAME" npm install
echo "Launched $APPLICATION_NAME"
