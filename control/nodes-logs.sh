#!/bin/bash
IN_NODE=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2pnode)
IN_BOT=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-bot-node)

readarray -t fields_nodes <<<"$IN_NODE"
readarray -t fields_bots <<<"$IN_BOT"

SEP=$(python3 -c "print('-' * 130)")

for node in "${fields_nodes[@]}" ;do
    printf '%s' "--- listing logs of node: $node ---"
    printf '\n\n'
    kubectl logs "$node"
    printf '\n%s\n' "$SEP"
done

for node in "${fields_bots[@]}" ;do
    printf '%s' "--- listing logs of node: $node ---"
    printf '\n\n'
    kubectl logs "$node"
    printf '\n%s\n' "$SEP"
done