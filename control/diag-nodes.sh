#!/bin/bash
SEP=$(python3 -c "print('-' * 130)")

IN_NODE=$(kubectl get po -o=name --field-selector=status.phase=Running | grep p2pnode)
IN_BOT=$(kubectl get po -o=name --field-selector=status.phase=Running | grep p2p-bot-node)
CMD='netstat -tlpn; netstat -tpn; ps -ef'

readarray -t fields_node <<<"${IN_NODE}"
readarray -t fields_bot <<<"${IN_BOT}"

for node in "${fields_node[@]}" ;do
    echo -e "$SEP\n--- diag for node: $node\n"
    kubectl exec $node -- bash -c $CMD
    echo ""
done
for node in "${fields_bot[@]}" ;do
    echo -e "$SEP\n--- diag for BOT node: $node\n"
    kubectl exec $node -- bash -c $CMD
    echo ""
done

exit 0