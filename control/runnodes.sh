#!/bin/bash
n0ip=$(kubectl get pods -o=jsonpath="{range .items[0]}{.status.podIP}{end}")
node_port=45666
n0=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep node-0)
nodes=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
bots=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-bot-node)

cmdstr="python3 /p2p/bot-node.py \`hostname -I\`:${node_port} ${n0ip}:${node_port}"

readarray -t fields_nodes <<<"$nodes"
readarray -t fields_bots <<<"$bots"

printf '\n%s\n' "debug: $cmdstr"

echo 'DEBUG:::: `hostname -I`:'"$node_port"' '"$n0ip"':'"$node_port"''

printf '%s\n' "--- running bot nodes"
for node in "${fields_bots[@]}" ;do
    printf '%s\n' "--- starting node: $node"
    kubectl exec $node -- bash -c '"'$cmdstr'"'
done

# printf '%s\n' "--- running default nodes"
# for node in "${fields_nodes[@]}" ;do
    # printf '%s\n' "--- starting node: $node"
    # kubectl exec -it $node -- bash -c 'python3 /p2p/node.py `hostname -I`'"$node_port"''
# done

exit 0


# kubectl exec -it p2p-bot-node-5d8f7767cf-psncc -- bash -c 'python3 /p2p/bot-node.py `hostname -I`:45666 172.17.0.13:45666'

