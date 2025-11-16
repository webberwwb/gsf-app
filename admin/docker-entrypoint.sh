#!/bin/sh
# Replace PORT in nginx config with actual PORT from environment
PORT=${PORT:-8080}
sed -i "s/listen .*/listen ${PORT};/" /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'

