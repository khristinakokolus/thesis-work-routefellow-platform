#!/bin/bash
declare -r NETWORK="travel-app-network"

docker build --tag insert-update-tickets-data -f Dockerfile.insert_update_tickets .
docker run -d --name insert-update-tickets-data -p 5003:5000 --network ${NETWORK} insert-update-tickets-data
