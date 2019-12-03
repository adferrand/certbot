#!/bin/bash
set -xe

if [[ "$OS_TYPE" == "centos" ]]; then
    yum install -y httpd
elif [[ "$OS_TYPE" == "ubuntu" ]]; then
    apt-get update && apt-get install -y apache2
fi

./letsencrypt-auto -n \
    --server ${DIRECTORY_URL} \
    --no-verify-ssl \
    --http-01-port ${HTTP_01_PORT} \
    --manual-public-ip-logging-ok \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email \
    --debug \
    -vv \
    --authenticator apache \
    --installer apache \
    -d test.${LE_SUFFIX}
