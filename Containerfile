FROM debian:stable-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends openssh-server ca-certificates git iputils-ping curl wget \
  && git config --global credential.helper store \
  && mkdir -p /workspace \
  && printf '%s\n' \
  'Port 2222' \
  'PermitRootLogin prohibit-password' \
  'PasswordAuthentication no' \
  'KbdInteractiveAuthentication no' \
  'AuthorizedKeysFile .ssh/authorized_keys' \
  'AllowAgentForwarding no' \
  'AllowTcpForwarding local' \
  'Subsystem sftp internal-sftp' \
  > /etc/ssh/sshd_config

WORKDIR /workspace

CMD bash -lc '\
  mkdir -p /run/sshd /root/.ssh && \
  chmod 700 /root/.ssh && \
  test -f /etc/ssh/hostkeys/ssh_host_ed25519_key || ssh-keygen -q -t ed25519 -N "" -f /etc/ssh/hostkeys/ssh_host_ed25519_key && \
  exec /usr/sbin/sshd -D -e -h /etc/ssh/hostkeys/ssh_host_ed25519_key'
