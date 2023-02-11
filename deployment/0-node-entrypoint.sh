#!/bin/sh

nmap -n -sn 10.244.1-2.0-30 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips.txt;

python3 /p2p/init.py;