#!/bin/sh
printf '%s\n' "--- terminating/removing current stack.."
kubectl delete deploy p2pnode && kubectl delete svc p2pnode-connector
printf '%s\n\n' "--- done ---"
printf '%s\n' "--- removing current image from minikube.."
minikube image rm 192.168.49.1:5000/p2p:1.0
printf '%s\n\n' "--- done ---"
printf '%s\n' "--- building docker image.."
docker image build -t 192.168.49.1:5000/p2p:1.0 ./
printf '%s\n\n' "--- done ---"
printf '%s\n' "--- loading docker image to minikube.."
minikube image load 192.168.49.1:5000/p2p:1.0 --daemon
printf '%s\n\n' "--- done ---"
printf '%s\n' "--- deploying pods.."
DEPLOYMENT_PATH=$(find node-deployment.yaml /home/${USER}/projects/ -name "node-deployment.yaml" -type f 2>/dev/null)
kubectl apply -f "$DEPLOYMENT_PATH"
printf '%s\n\n' "--- done ---"
exit 0