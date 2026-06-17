# mTLS Demo Website

Small FastAPI demo service with a client-certificate protected flag endpoint and
separate control endpoints.

## Certificate assumptions

Certificate generation is intentionally handled outside this app. The container
expects these files to be mounted read-only:

- `/run/mtls/server.crt`: server TLS certificate for the mTLS flag port.
- `/run/mtls/server.key`: private key for the server certificate.
- `/run/mtls/client.crt`: CA used to verify client certificates on `/flag`.

The paths can be overridden with `SERVER_CERT_FILE`, `SERVER_KEY_FILE`, and
`CLIENT_CA_FILE`.

The jump server should have its client certificate and key, plus whichever CA
certificate is needed to trust `/run/mtls/server.crt`.

## Endpoints

- `GET https://mtls-website:8443/flag`: requires a valid client certificate and returns the current flag, plus the latest non-revocation SOC report when one has been published.
- `POST http://mtls-website:8444/report`: raw body publishes a SOC report below the flag, separated by two newlines.
- `POST http://mtls-website:8444/revoke`: raw body replaces the `/flag` response with a SOC report and represents a credential revocation.
- `POST http://mtls-website:8444/pause`: `/flag` returns `Halting request, pending soc investigation`.
- `POST http://mtls-website:8444/resume`: `/flag` returns the stored flag again.
- `GET http://mtls-website:8444/health`: control-plane health check.

## Example

```sh
curl --cacert /root/server-ca.crt \
  --cert /root/client.crt \
  --key /root/client.key \
  https://mtls-website:8443/flag

curl --data 'no compromised credentials found' \
  http://mtls-website:8444/report

curl --data 'credentials compromised; revocation required' \
  http://mtls-website:8444/revoke
```
