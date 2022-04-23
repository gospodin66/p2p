#!/bin/bash
IN=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
readarray -t fields <<<"$IN"
for node in "${fields[@]}" ;do
    printf '%s\n' "--- listing lsitening ports on node: ${node}"
    kubectl exec -it "$node" -- netstat -tlpn | grep 172.17
done
echo "done!"
exit 0
