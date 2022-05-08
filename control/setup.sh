#!/bin/sh
printf '%s\n' "--- building docker images.."
docker image build -t 192.168.49.1:5000/p2p:1.0   -f ../deployment/Dockerfile        /home/cheki/projects/python/p2p
docker image build -t 192.168.49.1:5000/p2p-0:1.0 -f ../deployment/Dockerfile-node-0 /home/cheki/projects/python/p2p
docker image build -t 192.168.49.1:5000/p2p-bot:1.0 -f ../deployment/Dockerfile-bot-node /home/cheki/projects/python/p2p
printf '%s\n\n' "--- done ---"
printf '%s\n' "--- loading docker images to minikube.."
minikube image load 192.168.49.1:5000/p2p:1.0 --daemon
minikube image load 192.168.49.1:5000/p2p-0:1.0 --daemon
minikube image load 192.168.49.1:5000/p2p-bot:1.0 --daemon
printf '%s\n\n' "--- done ---"
printf '%s\n' "--- deploying.."
DEPLOYMENT_PATH=$(find node-deployment.yaml /home/${USER}/projects/ -name "node-deployment.yaml" -type f 2>/dev/null)
kubectl apply -f "$DEPLOYMENT_PATH"
printf '%s\n\n' "--- done ---"
exit 0