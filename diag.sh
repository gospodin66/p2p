#!/bin/bash
IN=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
readarray -t fields <<<"$IN"
SEP=$(python3 -c "print('-' * 140)")
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
printf '%s\n' "--- listing services ---"
kubectl get svc -o wide
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing running pods ---"
kubectl get pods -o wide --field-selector=status.phase=Running
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing pv ---"
kubectl get pv -o wide
printf '\n%s\n' "$SEP"
printf '%s\n' "--- listing pvc ---"
kubectl get pvc -o wide
printf '\n%s\n' "$SEP"
exit 0
