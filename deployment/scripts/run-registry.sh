#!/bin/sh

docker container stop p2p-image-registry;
docker container rm p2p-image-registry;
docker run \
       -dit \
       --ip 172.21.5.50 \
       --publish 127.0.0.1:47776:47777/tcp \
       --publish 127.0.0.1:47778:80/tcp \
       --publish 127.0.0.1:47780:443/tcp \
       --privileged \
       --network p2p-net \
       --name p2p-image-registry \
       p2p-image-registry:1.0 

docker exec -it p2p-image-registry /bin/sh