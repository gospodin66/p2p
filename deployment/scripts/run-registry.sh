#!/bin/sh

docker container stop p2p-image-registry;
docker container rm p2p-image-registry;
docker run \
       -dit \
       --publish 127.0.0.1:47776:47777/tcp \
       --publish 127.0.0.1:47778:80/tcp \
       --privileged \
       --network p2p-net \
       --name p2p-image-registry \
       p2p-image-registry:1.0 

docker exec -it p2p-image-registry /bin/sh