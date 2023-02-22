FROM python:3.10.5-alpine

RUN apk update && apk add --no-cache \
                          strace \
                          nano \
                          curl \
                          tor \
                          net-tools
                      
RUN mkdir -m 0700 /p2p/ && \
    mkdir -p /p2p/cstmcrypt/RSA-keys && \
    mkdir -p /p2p/cstmcrypt/AES-keys

COPY ./deployment/src/bot-node/ /p2p/
COPY ./deployment/docker-entrypoint.sh /entrypoint.sh

RUN chmod 0700 /p2p/node.py && \
    chmod 0700 /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "python3", "/p2p/node.py", "45666" ]
