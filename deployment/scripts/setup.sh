#!/bin/sh

PROJECTS_PATH="/home/${USER}/projects"

printf '%s\n' "--- building docker images.."
if ! docker image build -t p2p-0-node:1.0   -f ../Dockerfile-0-node   ${PROJECTS_PATH}/p2p/ || \
   ! docker image build -t p2p-bot-node:1.0 -f ../Dockerfile-bot-node ${PROJECTS_PATH}/p2p/
then
    printf '%s\n\n' "--- error building docker images ---"
    exit 1
else
    printf '%s\n\n' "--- done ---"
fi

printf '%s\n' "--- loading docker images to kind.."
if ! kind load docker-image p2p-0-node:1.0 || ! kind load docker-image p2p-bot-node:1.0
then
    printf '%s\n\n' "--- error loading docker images to kind: \
    p2p-def-node: $k_cmd_1 \
    p2p-0-node: $k_cmd_2 \
    p2p-bot-node: $k_cmd_3 \
    ---"
    exit 1
else
    printf '%s\n\n' "--- done ---"
fi

kubectl create namespace p2p



################ HELM ###############

printf '%s\n\n' "--- installing chart ---"
cd /home/cheki/projects/p2p/deployment/scripts
helm install p2p-net -f ../p2p-net/values.yaml ../p2p-net
printf '%s\n\n' "--- done ---"

############## MINIKUBE #############
# printf '%s\n' "--- deploying 0.."
# NODE_0_DEPLOYMENT_PATH=$(find node-0.yaml ${PROJECTS_PATH} -name "node-0.yaml" -type f 2>/dev/null)
# if ! kubectl apply -f "$NODE_0_DEPLOYMENT_PATH"
# then
#     printf '%s\n\n' "--- error deploying node-0 ---"
#     exit 1
# else
#     printf '%s\n\n' "--- done ---"
#     sleep 5
# fi

# printf '%s\n' "--- deploying nodes.."
# DEPLOYMENT_PATH=$(find node-deployment.yaml ${PROJECTS_PATH} -name "node-deployment.yaml" -type f 2>/dev/null)
# if ! kubectl apply -f "$DEPLOYMENT_PATH"
# then
#     printf '%s\n\n' "--- error deploying nodes ---"
#     exit 1
# else
#     printf '%s\n\n' "--- done ---"
#     exit 0
# fi
