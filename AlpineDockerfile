FROM alpine:latest
RUN apk update && apk add python3
RUN mkdir /p2p/
COPY ./node.py /p2p/node.py
ENTRYPOINT ["python3", "/p2p/node.py"]