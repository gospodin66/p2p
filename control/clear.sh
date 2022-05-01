#!/bin/sh

DOCKER_IMG="192.168.49.1:5000/p2p:1.0"

printf '%s\n' "--- terminating/removing current stack.."
kubectl delete deploy p2pnode && kubectl delete svc p2pnode-connector
printf '%s\n\n' "--- done ---"

while :
do
    printf '%s\n' "--- removing current image from minikube.."
    minikube image rm $DOCKER_IMG
    if minikube image ls | grep "$DOCKER_IMG";
    then
        printf '%s\n' "--- waiting for conatiners to terminate.."
        sleep 3 # wait for containers to terminate
    else
        break
    fi
done

printf '%s\n\n' "--- done ---"
exit 0