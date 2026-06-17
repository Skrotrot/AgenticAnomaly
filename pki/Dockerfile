FROM almalinux:9

RUN dnf install -y openssl && dnf clean all

COPY --chmod=755 gen-certs.sh /usr/local/bin/gen-certs

ENTRYPOINT ["gen-certs"]
