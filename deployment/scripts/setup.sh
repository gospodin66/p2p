#!/bin/bash

ns="p2p"
chart="p2p-net"
path_prefix=$(find /home -type d -name "p2p")
node0=("p2p-0-node:1.0" "../Dockerfile-0-node.dockerfile")
bot_node=("p2p-bot-node:1.0" "../Dockerfile-bot-node.dockerfile")

printf '%s\n' "--- building docker images.."
if ! DOCKER_BUILDKIT=1 docker image build -t ${node0[0]} -f ${node0[1]} $path_prefix || \
   ! DOCKER_BUILDKIT=1 docker image build -t ${bot_node[0]} -f ${bot_node[1]} $path_prefix;
then
    printf '%s\n\n' "--- error building docker images ---"
    exit 1
fi

printf '%s\n' "--- loading docker images to k3s.."
if ! docker save ${node0[0]} | sudo k3s ctr images import - || \
   ! docker save ${bot_node[0]} | sudo k3s ctr images import -;
then
    printf '%s\n\n' "--- error loading docker images to k3s cluster."
    exit 1
fi

kubectl create namespace ${ns} 2>/dev/null
kubectl config set-context --current --namespace=${ns}

printf '%s\n\n' "--- installing chart ---"
helm install ${chart} -f ../${chart}/values.yaml ../${chart}
printf '%s\n\n' "--- done ---"
