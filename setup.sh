#!/bin/bash
printf '%s\n' "--- building docker image:"
docker image build -t 192.168.49.1:5000/p2p:1.0 ./
printf '%s\n' "--- done"

printf '%s\n' "--- loading docker image to minikube:"
minikube image load 192.168.49.1:5000/p2p:1.0 --daemon
printf '%s\n' "--- done"

printf '%s\n' "--- deploying pods:"
DEPLOYMENT_PATH=$(find node-deployment.yaml / -name "node-deployment.yaml" -type f 2>/dev/null)
kubectl apply -f "$DEPLOYMENT_PATH"
printf '%s\n' "--- done"

printf '%s\n' "--- success!"
exit 0