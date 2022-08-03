#!/bin/bash

IN_0_NODE=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node)
IN_BOT_NODE=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-bot-node)

readarray -t fields_0_node <<<"$IN_0_NODE"
readarray -t fields_bots <<<"$IN_BOT_NODE"
NAMESPACE="p2p"

SEP=$(python3 -c "print('-' * 130)")
if [ "$1" == "full" ];
then
    for node in "${fields_0_node[@]}" ;do
        printf '%s' "--- listing diagnostics of 0-node: $node ---"
        printf '\n\n'
        kubectl describe "$node"
        printf '\n%s\n' "$SEP"
    done
    for node in "${fields_bots[@]}" ;do
        printf '%s' "--- listing diagnostics of bot-node: $node ---"
        printf '\n\n'
        kubectl describe "$node"
        printf '\n%s\n' "$SEP"
    done
fi
printf '%s\n' "--- listing nodes ---"
kubectl get node -o wide --namespace=${NAMESPACE}
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing deployments ---"
kubectl get deploy -o wide --namespace=${NAMESPACE}
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing services ---"
kubectl get svc -o wide --namespace=${NAMESPACE}
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing ingresses ---"
kubectl get ingress -o wide --namespace=${NAMESPACE}
printf '\n'
# kubectl describe svc p2p-0-node-connector --namespace=${NAMESPACE}
# kubectl describe svc p2p-def-node-connector --namespace=${NAMESPACE}
# kubectl describe svc p2p-bot-node-connector --namespace=${NAMESPACE}
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing running pods ---"
kubectl get pods -o wide --field-selector=status.phase=Running --namespace=${NAMESPACE}
printf '\n%s\n' "$SEP"
# printf '%s\n' "--- listing pv ---"
# kubectl get pv -o wide --namespace=${NAMESPACE}
# printf '\n%s\n' "$SEP"
# printf '%s\n' "--- listing pvc ---"
# kubectl get pvc -o wide --namespace=${NAMESPACE}
# printf '\n%s\n' "$SEP"
exit 0
