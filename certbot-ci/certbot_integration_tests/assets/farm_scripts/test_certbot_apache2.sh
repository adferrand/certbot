#!/bin/bash
set -x

apt-get update
apt-get -y --no-upgrade install apache2
apt-get -y install realpath

CONFFILE=/etc/apache2/sites-available/000-default.conf
PUBLIC_HOSTNAME="test.${LE_SUFFIX}"
sed -i '/ServerName/ s/#ServerName/ServerName/' $CONFFILE
sed -i '/ServerName/ s/www.example.com/'"${PUBLIC_HOSTNAME}"'/' $CONFFILE
cat /etc/apache2/sites-available/000-default.conf

/certbot/tests/letstest/scripts/bootstrap_os_packages.sh
python3 -m venv /workspace/venv
/workspace/venv/bin/python /certbot/tools/pipstrap.py
/workspace/venv/bin/python /certbot/tools/pip_install_editable.py /certbot/acme /certbot/certbot /certbot/certbot-apache

/workspace/venv/bin/certbot \
  -v \
  --debug \
  --agree-tos \
  --renew-by-default \
  --redirect \
  --register-unsafely-without-email \
  --domain "${PUBLIC_HOSTNAME}" \
  --server "${DIRECTORY_URL}" \
  --http-01-port "${HTTP_01_PORT}"
