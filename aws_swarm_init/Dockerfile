FROM alpine:3.9.2

RUN apk -v --update add \
        openssl \
        python \
        py-pip \
        && \
    pip install boto3 && \
    pip install docker && \
    apk -v --purge del py-pip && \
    rm /var/cache/apk/*

ENV DOCKER_HOST unix:///var/run/docker.sock

COPY ./src/ /home/run/
WORKDIR /home/run

ENTRYPOINT ["./docker-entrypoint.sh"]