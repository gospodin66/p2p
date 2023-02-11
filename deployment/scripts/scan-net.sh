#!/bin/sh

mkdir /p2p/; \
touch /p2p/ips-scan.txt; \
nmap -vvv -n -sn 10.244.0-5.0-255 -oG - | awk '/Up$/{print $2}' | sort -V | tee /p2p/ips-scan.txt
