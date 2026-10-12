FROM debian:stable-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends openssh-server ca-certificates git iputils-ping curl wget python3 docker.io docker-cli docker-compose iptables \
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
  'HostKey /etc/ssh/hostkeys/ssh_host_ed25519_key' \
  > /etc/ssh/sshd_config

WORKDIR /workspace

COPY entrypoint.py /usr/local/bin/entrypoint.py

CMD ["python3", "/usr/local/bin/entrypoint.py"]