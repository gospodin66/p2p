#!/bin/bash
IN=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
readarray -t fields <<<"$IN"
separator='------------------------------------'
for node in "${fields[@]}" ;do
    printf '%s' "--- listing diagnostics of node: ${node}"
    printf '\n\n'
    kubectl describe "${node}"
    printf '\n'
    printf '%s\n' "${separator}" 
done
echo "--- listing pv"
kubectl get pv -o wide
echo "--- listing pvc"
kubectl get pvc -o wide
echo "--- listing running pods"
kubectl get pods -o wide --field-selector=status.phase=Running
exit 0
