#!/bin/bash

node_port=45666

n0ip=$(kubectl get pods -o=jsonpath="{range .items[0]}{.status.podIP}{end}")
n0=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0)
nodes=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep def-node)
bots=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep bot-node)

readarray -t fields_nodes <<<"$nodes"
readarray -t fields_bots <<<"$bots"

printf '%s\n' "--- running bot nodes"
cnt=1
for node in "${fields_bots[@]}" ;do
    node_ip=$(kubectl get po -o=jsonpath="{range .items[${cnt}]}{.status.podIP}{end}")

    printf '%s\n' "--- starting bot ${cnt}: $node | $node_ip"

    cmdstr="python3 /p2p/node.py ${node_ip}:${node_port} ${n0ip}:${node_port} &"
    kubectl exec $node -- bash -c "$cmdstr"
    ((cnt++))
done

printf '%s\n' "--- running default nodes"
for node in "${fields_nodes[@]}" ;do
    node_ip=$(kubectl get po -o=jsonpath="{range .items[${cnt}]}{.status.podIP}{end}")

    printf '%s\n' "--- starting node ${cnt}: $node | $node_ip"

    cmdstr="python3 /p2p/init.py ${node_ip}:${node_port} ${n0ip}:${node_port} &"
    kubectl exec $node -- bash -c "$cmdstr"
    ((cnt++))
done

exit 0

# cmdtonode:172.17.0.2:45666|curl -L https://google.com
# kubectl exec p2p-bot-node-78b8d965c4-6gfzl -- bash -c 'python3 /p2p/node.py `hostname -I`:45666 172.17.0.12:45666'

