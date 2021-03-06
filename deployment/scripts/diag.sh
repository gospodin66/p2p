#!/bin/bash
IN=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
readarray -t fields <<<"$IN"
SEP=$(python3 -c "print('-' * 130)")
if [ "$1" == "full" ];
then
    for node in "${fields[@]}" ;do
        printf '%s' "--- listing diagnostics of node: $node ---"
        printf '\n\n'
        kubectl describe "$node"
        printf '\n%s\n' "$SEP"
    done
fi
printf '%s\n' "--- listing nodes ---"
kubectl get node -o wide
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing deployments ---"
kubectl get deploy -o wide
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing services ---"
kubectl get svc -o wide
printf '\n'
kubectl describe svc p2p-0-node-connector
kubectl describe svc p2p-def-node-connector
kubectl describe svc p2p-bot-node-connector
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing running pods ---"
kubectl get pods -o wide --field-selector=status.phase=Running
printf '\n%s\n' "$SEP"
# printf '%s\n' "--- listing pv ---"
# kubectl get pv -o wide
# printf '\n%s\n' "$SEP"
# printf '%s\n' "--- listing pvc ---"
# kubectl get pvc -o wide
# printf '\n%s\n' "$SEP"
exit 0
