FROM python:3.8-slim-buster

RUN apt update && apt install \
                        strace \
                        curl \
                        tor \
                        net-tools \
                        ffmpeg libsm6 libxext6 -y

RUN useradd -rm \
    -d /home/bot \
    -s /bin/bash \
    -g root \
    -G sudo \
    -u 10111 \
    bot
RUN echo "bot:bot" | chpasswd

RUN mkdir -m 0700 /p2p/ && \
    mkdir -p /p2p/cstmcrypt/RSA-keys && \
    mkdir -p /p2p/cstmcrypt/AES-keys

COPY ./deployment/src/bot-node/ /p2p/
COPY ./deployment/docker-entrypoint.sh /p2p/entrypoint.sh
COPY ./deployment/src/bot-node/assets/requirements.txt /p2p/requirements.txt

RUN chmod 0700 /p2p/node.py && \
    chmod 0700 /p2p/entrypoint.sh && \
    chown -R 10111:10111 /p2p/

# opencv for vcap
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /p2p/requirements.txt

USER bot

ENTRYPOINT [ "/p2p/entrypoint.sh" ]
CMD [ "python3", "/p2p/node.py", "45666" ]
