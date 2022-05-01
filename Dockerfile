FROM ubuntu:latest
RUN apt update && apt install python3 strace nano net-tools netcat curl -y
RUN mkdir -m 0700 /p2p/
COPY ./inputthread.py /p2p/inputthread.py
COPY ./node.py /p2p/node.py
RUN chmod 0700 /p2p/inputthread.py /p2p/node.py
#ENTRYPOINT ["python3", "/p2p/node.py"]