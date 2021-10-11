#!/usr/bin/env bash

docker build -t wannajoinfun .
docker tag wannajoinfun registry.digitalocean.com/arvid/wannajoinfun
docker push registry.digitalocean.com/arvid/wannajoinfun

echo "ssh root@api.wannajoin.fun, install docker, log in to the registry, install docker-compose, copy over docker-compose.yml, run docker-compose up -d, docker pull registry.digitalocean.com/arvid/wannajoinfun"
