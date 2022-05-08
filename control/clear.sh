#!/bin/sh

DOCKER_IMG="192.168.49.1:5000/p2p:1.0"
DOCKER_IMG_0="192.168.49.1:5000/p2p-0:1.0"
DOCKER_IMG_BOT="192.168.49.1:5000/p2p-bot:1.0"

printf '%s\n' "--- terminating/removing current stack.."
kubectl delete deploy p2pnode p2p-bot-node && \
kubectl delete svc p2pnode-connector p2p-bot-node-connector && \
kubectl delete --all po --namespace=p2p
printf '%s\n\n' "--- done ---"

while :
do
    printf '%s\n' "--- removing current image from minikube.."
    minikube image rm $DOCKER_IMG $DOCKER_IMG_0 $DOCKER_IMG_BOT
    if minikube image ls | grep "$DOCKER_IMG" || minikube image ls | "$DOCKER_IMG_0" || minikube image ls | "$DOCKER_IMG_BOT";
    then
        printf '%s\n' "--- waiting for conatiners to terminate.."
        sleep 3 # wait for containers to terminate
    else
        break
    fi
done

printf '%s\n\n' "--- done ---"
exit 0