#!/bin/bash

set -u

HALT_MESSAGE='Halting request, pending soc investigation'

docker exec agenticanomaly-jump-server-1 /usr/bin/cat /root/client.key > client.key
docker exec agenticanomaly-jump-server-1 /usr/bin/cat /root/client.crt > client.crt

while true; do
  response="$(curl -sk --cert client.crt --key client.key https://localhost:8443/flag)"
  printf '%s\n' "$response"

  if ! grep -Fq "$HALT_MESSAGE" <<<"$response"; then
    exit 0
  fi

  sleep 1
done
