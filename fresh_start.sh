#!/bin/bash

set -e

# Tear down existing containers, remove volume
docker-compose -f docker-compose-local.yml down
docker volume rm openoversight_postgres || true

# Start up and populate fields
docker-compose -f docker-compose-local.yml run --rm web python ../create_db.py
docker-compose -f docker-compose-local.yml run --rm web flask make-admin-user
docker-compose -f docker-compose-local.yml run --rm web flask add-department "Seattle Police Department" "SPD"
docker-compose -f docker-compose-local.yml run --rm web flask bulk-add-officers /data/init_data.csv
