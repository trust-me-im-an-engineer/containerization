#!/usr/bin/env python3
"""Connect SSH to a container's current Docker-published port."""

import json
import os
import socket
import subprocess
import sys
import threading


def copy_input(connection):
    try:
        while data := os.read(0, 65536):
            connection.sendall(data)
    finally:
        connection.shutdown(socket.SHUT_WR)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: ssh-proxy.py CONTAINER_NAME")
    container = sys.argv[1]
    details = json.loads(subprocess.check_output(
        ["docker", "inspect", container], text=True, stderr=subprocess.DEVNULL,
    ))[0]
    if not details["State"]["Running"]:
        raise SystemExit(f"{container} is not running")
    published = (details["NetworkSettings"]["Ports"] or {}).get("2222/tcp") or []
    ports = [binding["HostPort"] for binding in published
             if binding["HostIp"] == "127.0.0.1"]
    if len(ports) != 1:
        raise SystemExit(f"{container} has no unique localhost SSH port")

    with socket.create_connection(("127.0.0.1", int(ports[0]))) as connection:
        sender = threading.Thread(target=copy_input, args=(connection,), daemon=True)
        sender.start()
        while data := connection.recv(65536):
            os.write(1, data)


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as error:
        raise SystemExit(f"SSH container connection failed: {error}") from error
