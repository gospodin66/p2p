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
       --publish 127.0.0.1:47776:47777/tcp \
       --publish 127.0.0.1:47780:443/tcp \
       --publish 127.0.0.1:47778:80/tcp \
       --publish 127.0.0.1:47722:22/tcp \
       --publish 192.168.170.1:47722:22/tcp \
       --privileged \
       --network p2p-net \
       --name p2p-image-registry \
       p2p-image-registry:1.0 

docker exec -it p2p-image-registry /bin/sh
