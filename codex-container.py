#!/usr/bin/env python3
"""Start a project container and add its SSH host."""

import argparse
import os
import re
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
address = subprocess.check_output(compose + ["port", "dev", "2222"], env=env, text=True).strip()
port = address.rsplit(":", 1)[1]

ssh = Path.home() / ".ssh"
hosts = ssh / "codex-containers.d"
hosts.mkdir(parents=True, exist_ok=True)
include = "Include ~/.ssh/codex-containers.d/*.conf\n"
config = ssh / "config"
current = config.read_text() if config.exists() else ""
if include.strip() not in current.splitlines():
    config.write_text(include + current)

(hosts / f"{name}.conf").write_text(
    f"Host {name}\n"
    "  HostName 127.0.0.1\n"
    f"  Port {port}\n"
    "  User root\n"
    "  IdentityFile ~/.ssh/id_ed25519\n"
)
print(f"Connect to {name} in VS Code, or run: ssh {name}")
