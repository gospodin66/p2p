FROM python:3.10.5-alpine

RUN apk update && apk add --no-cache \
                          strace \
                          nano \
                          net-tools \
                          curl \
                          openssh-client \
                          nmap \
                          perl \
                          expect

RUN mkdir -m 0700 /p2p/ && \
    mkdir -p /p2p/cstmcrypt/RSA-keys && \
    mkdir -p /p2p/cstmcrypt/AES-keys

COPY ./deployment/src/0-node /p2p/
COPY ./deployment/docker-entrypoint.sh /entrypoint.sh

RUN touch /p2p/ips.txt && \
    chmod 0700 /p2p/init.py && \
    chmod 0600 /p2p/ips.txt && \
    chmod 0700 /p2p/assets/automate && \
    chmod 0700 /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "expect", "/p2p/assets/automate", "45666", "10.244.1-2.2-255" ]
