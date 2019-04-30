#!/bin/sh
set -xe

cd letsencrypt
./certbot-auto -v -n --os-packages-only
./tools/venv.py
. venv/bin/activate

certbot --version
