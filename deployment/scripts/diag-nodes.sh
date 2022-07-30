#!/bin/bash
SEP=$(python3 -c "print('-' * 130)")

IN_0_NODE=$(kubectl get po -o=name --field-selector=status.phase=Running | grep p2p-0-node)
IN_DEF_NODE=$(kubectl get po -o=name --field-selector=status.phase=Running | grep p2p-def-node)
IN_BOT_NODE=$(kubectl get po -o=name --field-selector=status.phase=Running | grep p2p-bot-node)
CMD='netstat -tlpn; netstat -tpn; ps -ef'

readarray -t fields_node <<<"${IN_DEF_NODE}"
readarray -t fields_bot <<<"${IN_BOT_NODE}"
readarray -t fields_0 <<<"${IN_0_NODE}"

for node in "${fields_node[@]}" ;do
    echo -e "$SEP\n--- diag for DEF node: $node\n"
    kubectl exec $node -- /bin/sh -c $CMD
    echo ""
done
for node in "${fields_bot[@]}" ;do
    echo -e "$SEP\n--- diag for BOT node: $node\n"
    kubectl exec $node -- /bin/sh -c $CMD
    echo ""
done
for node in "${fields_0[@]}" ;do
    echo -e "$SEP\n--- diag for 0 node: $node\n"
    kubectl exec $node -- /bin/sh -c $CMD
    echo ""
done

exit 0