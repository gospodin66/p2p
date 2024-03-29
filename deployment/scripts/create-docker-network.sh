#!/bin/sh

docker network create \
  --attachable \
  --driver=overlay \
  --subnet=172.21.0.0/16 \
  --ip-range=172.21.5.0/24 \
  --gateway=172.21.5.254 \
  p2p-net


docker network create \
  --attachable \
  --driver=overlay \
  --subnet=10.42.0.0/24 \
  --ip-range=10.42.0.0/24 \
  --gateway=10.42.0.254 \
  p2p-net-gateway