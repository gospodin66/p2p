FROM python:3.10.5-alpine

RUN apk update && apk add --no-cache \
                          strace \
                          net-tools \
                          curl

COPY ./deployment/src/0-node /p2p/
COPY ./deployment/docker-entrypoint.sh /entrypoint.sh

RUN chmod 0700 /p2p/init.py && \
    chmod 0700 /p2p/assets/automate && \
    chmod 0700 /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "/bin/sh" ]
