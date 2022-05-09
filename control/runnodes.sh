#!/bin/bash
n0ip=$(kubectl get pods -o=jsonpath="{range .items[0]}{.status.podIP}{end}")
node_port=45666
n0=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0)
nodes=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
bots=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-bot-node)

readarray -t fields_nodes <<<"$nodes"
readarray -t fields_bots <<<"$bots"

printf '%s\n' "--- running bot nodes"
cnt=1
for node in "${fields_bots[@]}" ;do
    printf '%s\n' "--- starting bot ${cnt}: $node"
    node_ip=$(kubectl get pods -o=jsonpath="{range .items[${cnt}]}{.status.podIP}{end}")
    cmdstr="python3 /p2p/bot-node.py ${node_ip}:${node_port} ${n0ip}:${node_port} &"
    kubectl exec $node -- bash -c "$cmdstr"
    ((cnt++))
done

printf '%s\n' "--- running default nodes"
for node in "${fields_nodes[@]}" ;do
    printf '%s\n' "--- starting node: $node"
    node_ip=$(kubectl get pods -o=jsonpath="{range .items[${cnt}]}{.status.podIP}{end}")
    cmdstr="python3 /p2p/node.py ${node_ip}:${node_port} ${n0ip}:${node_port} &"
    kubectl exec $node -- bash -c "$cmdstr"
done

exit 0


# kubectl exec -it p2p-bot-node-5d8f7767cf-psncc -- bash -c 'python3 /p2p/bot-node.py `hostname -I`:45666 172.17.0.13:45666'

