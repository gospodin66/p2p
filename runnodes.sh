#!/bin/bash
IN=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
readarray -t fields <<<"$IN"
for node in "${fields[@]}" ;do
    printf '%s\n' "--- POSIX representation of str:"
    printf '%s\n' "$node" | od -vtc -to1
    printf '%s\n' "--- HEX representation of str:"
    printf '%s\n' "$node" | xxd
    printf '%s\n' "--- attaching to node: ${node}"
    kubectl attach -it -c p2pnode-alpine "$node"
done
echo "done!"
exit 0
