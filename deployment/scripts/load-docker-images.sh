
#!/bin/sh
PROJECTS_PATH="/home/cheki/projects"
docker image build -t p2p-0-node:1.0   -f ../Dockerfile-0-node   ${PROJECTS_PATH}/p2p/ && \
docker image build -t p2p-image-registry:1.0 -f ../Dockerfile-docker-img-registry ${PROJECTS_PATH}/p2p/ && \
docker image build -t p2p-bot-node:1.0 -f ../Dockerfile-bot-node ${PROJECTS_PATH}/p2p/