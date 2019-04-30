#!/bin/sh
set -xe

cd letsencrypt
./certbot-auto -v -n --debug --version
