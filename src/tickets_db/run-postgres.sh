#!/bin/bash

declare -r NETWORK="travel-app-network"

if docker network create --driver bridge ${NETWORK}; then
   echo "Successfully created network ${NETWORK}"
else
   echo "Such network ${NETWORK} already exists"
fi

if docker run --name postgres-db-tickets --network ${NETWORK} -e POSTGRES_USER=test_user -e POSTGRES_DB=tickets_db -e POSTGRES_PASSWORD=1234 -p 5433:5432 -v "$(pwd)"/tickets_db/create_tables.sql:/docker-entrypoint-initdb.d/create_tables.sql -d postgres:latest; then
   echo "Successfully launched Postgres db"
else
   echo "Postgres container already exists"
fi

