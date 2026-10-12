#!/usr/bin/env python3
"""Run SSH and an inner Docker daemon, stopping nested containers cleanly."""

import os
import signal
import subprocess
import shutil
import time
from pathlib import Path

DOCKER_FLAGS = [
    "dockerd",
    "--iptables=false",
    "--ip6tables=false",
    "--storage-driver=vfs",
]
HOST_KEY = Path("/etc/ssh/hostkeys/ssh_host_ed25519_key")
shutdown_requested = False


def request_shutdown(signum, _frame):
    global shutdown_requested
    shutdown_requested = True


def stop_process(process, name, timeout=15):
    if process.poll() is not None:
        return
    print(f"Stopping {name}...", flush=True)
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"{name} did not exit; killing it", flush=True)
        process.kill()
        process.wait()


def main():
    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)

    Path("/run/sshd").mkdir(parents=True, exist_ok=True)
    
    ssh_dir = Path("/root/.ssh")
    ssh_dir.mkdir(parents=True, exist_ok=True)
    ssh_dir.chmod(0o700)

    authorized_keys = ssh_dir / "authorized_keys"

    shutil.copyfile(
        "/tmp/ssh-authorized-key",
        authorized_keys
    )

    authorized_keys.chmod(0o600)

    HOST_KEY.parent.mkdir(parents=True, exist_ok=True)
    if not HOST_KEY.is_file():
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(HOST_KEY)],
            check=True,
        )

    with open("/var/log/dockerd.log", "a") as docker_log:
        docker = subprocess.Popen(DOCKER_FLAGS, stdout=docker_log, stderr=subprocess.STDOUT)
        try:
            ssh = subprocess.Popen(
                ["/usr/sbin/sshd", "-D", "-e", "-h", str(HOST_KEY)]
            )
        except BaseException:
            stop_process(docker, "Docker")
            raise

        try:
            while not shutdown_requested:
                if docker.poll() is not None:
                    print("dockerd exited unexpectedly; see /var/log/dockerd.log", flush=True)
                    break
                if ssh.poll() is not None:
                    print("sshd exited unexpectedly", flush=True)
                    break
                time.sleep(0.5)
        finally:
            # Prevent new SSH sessions while nested containers are shutting down.
            stop_process(ssh, "SSH")
            if docker.poll() is None:
                try:
                    result = subprocess.run(
                        ["docker", "ps", "-q"],
                        capture_output=True, text=True, timeout=10, check=True,
                    )
                    container_ids = result.stdout.split()
                    if container_ids:
                        print("Stopping nested containers...", flush=True)
                        subprocess.run(
                            ["docker", "stop", "--time", "30", *container_ids],
                            timeout=45, check=False,
                        )
                except (OSError, subprocess.SubprocessError) as error:
                    print(f"Could not stop all nested containers gracefully: {error}", flush=True)
            stop_process(docker, "Docker")


if __name__ == "__main__":
    main()

