#!/bin/bash

ns="p2p"
chart="p2p-net"
path_prefix="/home/${USER}/projects/p2p/"
node0=("p2p-0-node:1.0" "../Dockerfile-0-node.dockerfile")
bot_node=("p2p-bot-node:1.0" "../Dockerfile-bot-node.dockerfile")
probe_node=("p2p-probe-node:1.0" "../Dockerfile-probe.dockerfile")

printf '%s\n' "--- building docker images.."
if ! docker image build -t ${node0[0]} -f ${node0[1]} $path_prefix || \
   ! docker image build -t ${bot_node[0]} -f ${bot_node[1]} $path_prefix || \
   ! docker image build -t ${probe_node[0]} -f ${probe_node[1]} $path_prefix 
then
    printf '%s\n\n' "--- error building docker images ---"
    exit 1
fi

printf '%s\n' "--- loading docker images to kind.."
if ! kind load docker-image ${node0[0]} || \
   ! kind load docker-image ${bot_node[0]} || \
   ! kind load docker-image ${probe_node[0]}
then
    printf '%s\n\n' "--- error loading docker images to kind cluster."
    exit 1
fi

kubectl create namespace ${ns} 2>/dev/null
kubectl config set-context --current --namespace=${ns}

printf '%s\n\n' "--- installing chart ---"
helm install ${chart} -f ../${chart}/values.yaml ../${chart}
printf '%s\n\n' "--- done ---"
