#!/bin/bash
IN_0_NODE=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-0-node)
IN_BOT_NODE=$(kubectl get pods -o=name --field-selector=status.phase=Running | grep p2p-bot-node)

readarray -t fields_0_node <<<"$IN_0_NODE"
readarray -t fields_bot_node <<<"$IN_BOT_NODE"

SEP=$(python3 -c "print('-' * 130)")

for node in "${fields_0_node[@]}" ;do
    printf '%s' "--- listing logs of node: $node ---"
    printf '\n\n'
    kubectl logs "$node"
    printf '\n%s\n' "$SEP"
done

for node in "${fields_bot_node[@]}" ;do
    printf '%s' "--- listing logs of node: $node ---"
    printf '\n\n'
    kubectl logs "$node"
    printf '\n%s\n' "$SEP"
done