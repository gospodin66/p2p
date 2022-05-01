#!/bin/sh
if [ $(hostname -i) != "127.0.1.1" ];
then
    python3 -c 'print("connnode:127.0.0.1:45666\n")' | python3 node.py 127.0.0.1 45555
else
    python3 -c 'print("connnode:127.0.0.1:45555\n")' | python3 node.py 127.0.0.1 45666
fi
