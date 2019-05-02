FROM centos:7

ENV container docker
ENV OS_TYPE centos

CMD ["/lib/systemd/systemd"]
