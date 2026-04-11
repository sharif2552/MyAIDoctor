#!/bin/bash
# init-ssl.sh — Run this ONCE on the server to bootstrap the Let's Encrypt certificate.
#
# Usage:
#   bash scripts/init-ssl.sh
#
# What it does:
#   1. Creates a temporary self-signed cert so nginx can start (nginx refuses to start
#      if ssl_certificate files are missing).
#   2. Starts nginx.
#   3. Runs certbot to get the real Let's Encrypt certificate via the HTTP-01 challenge.
#   4. Reloads nginx with the real certificate.

set -e

DOMAIN="seliseproject.sharifsdevlab.me"
EMAIL="sharifhossain4888@gmail.com" 

CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

echo "==> Checking for existing certificate..."
if docker compose run --rm certbot certificates 2>/dev/null | grep -q "$DOMAIN"; then
  echo "Certificate already exists for $DOMAIN. Nothing to do."
  exit 0
fi

echo "==> Creating temporary self-signed certificate so nginx can start..."
docker compose run --rm --entrypoint "" certbot sh -c "
  mkdir -p /etc/letsencrypt/live/$DOMAIN && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
    -out    /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
    -subj '/CN=localhost'
"

echo "==> Starting nginx with temporary certificate..."
docker compose up -d nginx

echo "==> Waiting for nginx to be ready..."
sleep 3

echo "==> Obtaining real Let's Encrypt certificate..."
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "==> Reloading nginx with real certificate..."
docker compose exec nginx nginx -s reload

echo ""
echo "Done! HTTPS is now active for https://$DOMAIN"
echo "Certbot will auto-renew the certificate every 12 hours via the certbot container."
