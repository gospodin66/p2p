#!/bin/sh

# SERVICE_PORTS=$(kubectl describe service --namespace=p2p | grep -i nodeport | grep -o -E '[0-9]+');
# readarray -t fields <<<"${SERVICE_PORTS}";
# echo "$fields[0]";

#additional arg: p2p-0-node-connector:45555
python3 /p2p/node.py 45666