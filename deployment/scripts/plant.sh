#!/bin/sh

######## VIA SVC PORT
# path="node-autorun.py"
# host="$(hostname -i):45666"
# remotehost="172.19.0.3:31515"
# if [ ! -f $path ]; then wget -O $path http://$remotehost; fi
# if [ ! -f $path ]; then curl -vvv -o $path http://$remotehost; fi
# python $path $host $remotehost

######## VIA POD PORT
path="node-autorun.py"
host="$(hostname -i):45666"
remotehost="10.244.1.116:45666"
if [ ! -f $path ]; then wget -O $path http://$remotehost; fi
if [ ! -f $path ]; then curl -vvv -o $path http://$remotehost; fi
python $path $host $remotehost
