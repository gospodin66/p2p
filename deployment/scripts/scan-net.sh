#!/bin/sh

mkdir /p2p/; \
touch /p2p/ips-scan.txt; \
nmap -vvv -n -sn 10.42.0.1-255 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips-scan.txt
