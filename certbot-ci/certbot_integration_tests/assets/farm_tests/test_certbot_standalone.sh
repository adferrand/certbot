#!/bin/sh
set -xe

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
    --authenticator standalone \
    --installer null \
    -d test.${LE_SUFFIX}
