FROM ubuntu:latest
RUN apt update && apt install python3 -y
RUN mkdir /p2p/
COPY ./node.py /p2p/node.py
ENTRYPOINT ["python3", "/p2p/node.py"]