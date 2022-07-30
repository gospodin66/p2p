#!/bin/sh

nmap -n -sn 10.244.0.10-255 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips.txt;
python3 /p2p/init.py;