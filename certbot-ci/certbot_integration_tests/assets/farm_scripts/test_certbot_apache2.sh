#!/bin/bash
set -x

PUBLIC_HOSTNAME="test.${LE_SUFFIX}"

if apt-get -v >/dev/null 2>&1; then
  apt-get update
  apt-get -y --no-upgrade install apache2
  apt-get -y install realpath

  CONF_FILE=/etc/apache2/sites-available/000-default.conf
  sed -i '/VirtualHost/ s/*:80/*:'"${HTTP_01_PORT}"'/' "${CONF_FILE}"
  sed -i '/ServerName/ s/#ServerName/ServerName/' "${CONF_FILE}"
  sed -i '/ServerName/ s/www.example.com/'"${PUBLIC_HOSTNAME}"'/' "${CONF_FILE}"
  cat /etc/apache2/sites-available/000-default.conf
elif yum --version >/dev/null 2>&1; then
  setenforce 0 || true
  yum -y install httpd
  yum -y install nghttp2 || true
  /usr/libexec/httpd-ssl-gencerts
  service httpd start
  mkdir -p "/var/www/${PUBLIC_HOSTNAME}/public_html"
  chmod -R oug+rwx /var/www
  chmod -R oug+rw /etc/httpd
  echo '<html><head><title>foo</title></head><body>bar</body></html>' > "/var/www/${PUBLIC_HOSTNAME}/public_html/index.html"
  mkdir -p /etc/httpd/sites-available
  mkdir -p /etc/httpd/sites-enabled
  echo """
<VirtualHost *:${HTTP_01_PORT}>
    ServerName ${PUBLIC_HOSTNAME}
    DocumentRoot /var/www/${PUBLIC_HOSTNAME}/public_html
    ErrorLog /var/www/${PUBLIC_HOSTNAME}/error.log
    CustomLog /var/www/${PUBLIC_HOSTNAME}/requests.log combined
</VirtualHost>""" >> "/etc/httpd/conf.d/${PUBLIC_HOSTNAME}.conf"
fi

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
  --no-verify-ssl \
  --http-01-port "${HTTP_01_PORT}"
