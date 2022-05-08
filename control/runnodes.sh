#!/bin/sh
AUTO_CONNECT_CMD=$(cat ../assets/_node.txt)
NODE_TO_SKIP="p2pnode-79bd4b6cd8-qsp8d"

IN=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
readarray -t fields <<<"$IN"

for node in "${fields[@]}" ;do
    if [ "$node" == "pod/$NODE_TO_SKIP" ];
    then
        printf '%s\n' "--- skipping node: $node ---"
    else
        printf '%s\n' "--- starting node: $node ---"
        # auto-connect
        kubectl exec -it $node -- bash -c 'echo -n "'$AUTO_CONNECT_CMD'" | /p2p/node.py `hostname -I` 45666'
    fi
done
exit 0

# init as daemon
# kubectl exec p2pnode-79bd4b6cd8-qsp8d -- bash -c '/p2p/node.py `hostname -I` 45666 &'

# init 0. node (e.g. 172.17.0.6:45666)
# kubectl exec -it p2pnode-79bd4b6cd8-qsp8d -- bash -c '/p2p/node.py `hostname -I` 45666'

# init node with auto-connection to 0.
# kubectl exec -it p2pnode-79bd4b6cd8-qsp8d -- bash -c 'echo -n "connnode:172.17.0.3:45666" | /p2p/node.py `hostname -I` 45666'
