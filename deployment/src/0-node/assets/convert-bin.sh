#!/bin/sh
path_in="bot-node.py"
path_out="bot-node.bin"
cat "$path_in" | perl -lpe '$_=join " ", unpack"(B8)*"' > "$path_out"
