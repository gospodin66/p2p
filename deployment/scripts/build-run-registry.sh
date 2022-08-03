#!/bin/sh

PROJECT_PATH="/home/cheki/projects/p2p/"

docker container stop p2p-image-registry;

docker image build \
            -t p2p-image-registry:1.0 \
            -f ../Dockerfile-docker-img-registry \
            ${PROJECT_PATH}

docker run \
       -dit \
       --init \
       --rm \
       --ip 172.21.5.50 \
       --publish 192.168.1.61:47880:80/tcp \
       --publish 192.168.1.61:47443:443/tcp \
       --publish 192.168.1.61:47222:22/tcp \
       --privileged \
       --network p2p-net \
       --name p2p-image-registry \
       p2p-image-registry:1.0 

docker exec -it p2p-image-registry /bin/sh
