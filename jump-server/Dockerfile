FROM almalinux/9-init

# Set up elevated file read misconfiguration
COPY --chmod=755 show-log /usr/local/sbin/

RUN dnf install -y epel-release \
    && dnf install -y sudo inotify-tools openssh-server python3 \
    && dnf clean all

RUN useradd -m ctfuser
RUN passwd -d ctfuser

RUN echo "ctfuser ALL=(root) NOPASSWD: /usr/local/sbin/show-log *" >> /etc/sudoers

RUN echo 'Defaults logfile="/var/log/sudo.log"' >> /etc/sudoers \
    && touch /var/log/sudo.log \
    && chmod 0600 /var/log/sudo.log

COPY --chmod=777 info.txt /home/ctfuser/info.txt

# Set up security telemetry shipping
COPY --chmod=755 credential-watch.py /usr/local/sbin/credential-watch
COPY credential-watch.service /etc/systemd/system/credential-watch.service
RUN systemctl enable credential-watch.service

# Set up passwordless SSH for ctfuser
RUN printf 'ctfuser\n' > /etc/ssh/banner \
    && printf 'ctfuser\n' > /etc/motd \
    && printf '%s\n' \
        'PasswordAuthentication yes' \
        'PermitEmptyPasswords yes' \
        'PubkeyAuthentication no' \
        'ChallengeResponseAuthentication no' \
        'UsePAM no' \
        'Banner /etc/ssh/banner' \
        'AllowUsers ctfuser' \
        >> /etc/ssh/sshd_config \
    && systemctl enable sshd.service

CMD ["/sbin/init"]
