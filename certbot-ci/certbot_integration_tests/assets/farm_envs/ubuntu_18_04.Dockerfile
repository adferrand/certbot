FROM ubuntu:18.04

ENV container docker
ENV OS_TYPE ubuntu

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends systemd \
 && rm -rf /var/lib/apt/lists/*

CMD ["/lib/systemd/systemd"]
