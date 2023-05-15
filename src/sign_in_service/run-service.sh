#!/bin/bash
declare -r NETWORK="travel-app-network"

docker build --tag sign-in-service -f Dockerfile.sign_in .
docker run -d --name service-sign-in -p 5002:5000 --network ${NETWORK} --rm sign-in-service
