#!/usr/bin/env python3
"""Start or reload project container"""

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("project", type=Path, help="project directory to mount")
parser.add_argument("--name", help="Compose project and SSH host name (default: directory name)")
args = parser.parse_args()

project = args.project.expanduser().resolve()
if not project.is_dir():
    parser.error(f"project directory does not exist: {project}")

name = args.name or project.name
if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
    parser.error("name must start with a lowercase letter or digit and contain only lowercase letters, digits, hyphens, or underscores")

compose = ["docker", "compose", "-f", str(Path(__file__).with_name("compose.yml")), "-p", name]
env = os.environ.copy()
env["PROJECT_PATH"] = str(project)

subprocess.run(compose + ["up", "-d"], env=env, check=True)
container = f"{name}-dev"
details = json.loads(subprocess.check_output(
    ["docker", "inspect", container], text=True,
))[0]
if not details["State"]["Running"]:
    raise SystemExit(
        f"{container} exited after startup (exit code "
        f"{details['State']['ExitCode']}). Check `docker logs {container}` "
        "and the inner Docker log before trying to connect."
    )
published = (details["NetworkSettings"]["Ports"] or {}).get("2222/tcp") or []
localhost_ports = [binding["HostPort"] for binding in published
                   if binding["HostIp"] == "127.0.0.1"]
if len(localhost_ports) != 1:
    raise SystemExit(
        f"{container} is running without a published localhost SSH port. "
        "Docker did not restore its port mapping; check docker inspect before "
        "recreating the container."
    )
ssh = Path.home() / ".ssh"
hosts = ssh / "codex-containers.d"
hosts.mkdir(parents=True, exist_ok=True)
shutil.copyfile(Path(__file__).with_name("ssh-proxy.py"), hosts / "ssh-proxy.py")
include = "Include ~/.ssh/codex-containers.d/*.conf\n"
config = ssh / "config"
current = config.read_text() if config.exists() else ""
if include.strip() not in current.splitlines():
    config.write_text(include + current)

(hosts / f"{name}.conf").write_text(
    f"Host {name}\n"
    "  HostName 127.0.0.1\n"
    f"  ProxyCommand python3 ~/.ssh/codex-containers.d/ssh-proxy.py {container}\n"
    "  User root\n"
    "  IdentityFile ~/.ssh/id_ed25519\n"
)
print(f"Connect to {name} in VS Code, or run: ssh {name}")
