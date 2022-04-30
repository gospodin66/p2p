#!/bin/bash
NODE=$(cat ./_node.txt)
IN=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
readarray -t fields <<<"$IN"
for node in "${fields[@]}" ;do
    printf '%s\n' "--- attaching to node: $node ---"
    echo $NODE | xargs -n1 bash -c "kubectl attach $node -c p2pnode" kubectl $1
done
exit 0
