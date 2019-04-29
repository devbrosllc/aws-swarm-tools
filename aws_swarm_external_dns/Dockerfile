FROM alpine:3.9.2

RUN apk -v --update add \
        openssl \
        python \
        py-pip \
        && \
    pip install --upgrade awscli==1.14.5 && \
    pip install boto3 && \
    apk -v --purge del py-pip && \
    rm /var/cache/apk/*

ENV VERSION 0.7.3
ENV DOWNLOAD_URL https://github.com/jwilder/docker-gen/releases/download/$VERSION/docker-gen-alpine-linux-amd64-$VERSION.tar.gz
ENV DOCKER_HOST unix:///var/run/docker.sock

RUN wget -qO- $DOWNLOAD_URL | tar xvz -C /usr/local/bin
COPY ./docker-gen/ /home/run/
WORKDIR /home/run

CMD sleep 3000
#ENTRYPOINT ["./docker-entrypoint.sh"]