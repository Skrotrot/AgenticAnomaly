#!/bin/bash

set -euo pipefail

openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 \
  -noenc -keyout server.key -out server.crt -subj "/CN=mtls-website" \
  -addext "subjectAltName=DNS:mtls-website"

openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 \
  -noenc -keyout client.key -out client.crt -subj "/CN=jump-server"

mkdir -p /run/mtls/server
mkdir -p /run/mtls/client

cp client.key /run/mtls/client/
cp client.crt /run/mtls/client/
cp server.crt /run/mtls/client/

cp server.key /run/mtls/server/
cp server.crt /run/mtls/server/
cp client.crt /run/mtls/server/
