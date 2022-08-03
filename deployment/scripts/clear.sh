#!/bin/sh

DOCKER_IMG="docker.io/library/p2p-def-node:1.0"
DOCKER_IMG_0="docker.io/library/p2p-0-node:1.0"
DOCKER_IMG_BOT="docker.io/library/p2p-bot-node:1.0"
NAMESPACE="p2p"

printf '%s\n' "--- terminating/removing current stack.."
kubectl delete deploy p2p-bot-node \
                      p2p-0-node \
                      --namespace=${NAMESPACE} && \
kubectl delete svc p2p-0-node-connector \
                   p2p-bot-node-connector \
                   --namespace=${NAMESPACE} && \
kubectl delete --all po --namespace=${NAMESPACE}
printf '%s\n\n' "--- done ---"

# while :
# do
#     # printf '%s\n' "--- removing current image from minikube.."
#     # minikube image rm $DOCKER_IMG $DOCKER_IMG_0 $DOCKER_IMG_BOT
#     # if minikube image ls | grep "$DOCKER_IMG" || minikube image ls | grep "$DOCKER_IMG_0" || minikube image ls | grep "$DOCKER_IMG_BOT";

#     printf '%s\n' "--- removing current chart from kind.."
#     helm uninstall p2p-net 

#     if helm list | grep "p2p-net";
#     then
#         printf '%s\n' "--- waiting for conatiners to terminate.."
#         sleep 3 # wait for containers to terminate
#     else
#         break
#     fi
# done

printf '%s\n' "--- removing current chart from kind.."
helm uninstall p2p-net 

printf '%s\n\n' "--- done ---"
exit 0