#!/bin/bash
declare -r NETWORK="travel-app-network"

docker build --tag sign-up-service -f Dockerfile.sign_up .
docker run -d --name service-sign-up -p 5001:5000 --network ${NETWORK} --rm sign-up-service
