#!/bin/bash
set -xe

/certbot/tests/letstest/scripts/bootstrap_os_packages.sh
python3 -m venv /workspace/venv
/workspace/venv/bin/python /certbot/tools/pipstrap.py
/workspace/venv/bin/python /certbot/tools/pip_install_editable.py /certbot/acme /certbot/certbot

/workspace/venv/bin/certbot -n \
    --server "${DIRECTORY_URL}" \
    --no-verify-ssl \
    --http-01-port "${HTTP_01_PORT}" \
    --manual-public-ip-logging-ok \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email \
    --debug \
    -vv \
    --authenticator standalone \
    --installer null \
    -d "test.${LE_SUFFIX}"
