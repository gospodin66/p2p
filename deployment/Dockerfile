FROM ubuntu:latest

RUN apt update && apt install python3 strace nano net-tools netcat curl -y
RUN mkdir -m 0700 /p2p/

COPY ./app/def-node/inputthread.py /p2p/inputthread.py
COPY ./app/def-node/inputcallback.py /p2p/inputcallback.py
COPY ./app/def-node/node_fnc.py /p2p/node_fnc.py
COPY ./app/def-node/init.py /p2p/init.py
COPY ./app/def-node/node.py /p2p/node.py

RUN chmod 0700 /p2p/inputthread.py /p2p/init.py /p2p/inputcallback.py /p2p/node_fnc.py /p2p/init.py
