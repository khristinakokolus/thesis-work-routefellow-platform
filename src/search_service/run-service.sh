#!/bin/bash
declare -r NETWORK="travel-app-network"

docker build --tag search-service -f Dockerfile.search .
docker run -d --name service-search -p 5003:5000 --network ${NETWORK} search-service
