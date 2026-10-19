This container setup isolates codex from your host system. It does so by creating docker container with gvisor isolation and openssh-server inside. Connect your host vscode to the container via ssh to get a near-native development experience with isolation safety.

# Host Docker configuration

Configure the host Docker daemon's `runsc` runtime in `/etc/docker/daemon.json`:

```json
{
  "cgroup-parent": "docker_limit.slice",
  "runtimes": {
    "runsc": {
      "path": "/usr/local/bin/runsc",
      "runtimeArgs": [
        "--net-raw",
        "--allow-packet-socket-write",
        "--overlay2=none"
      ]
    }
  }
}
```

Merge these settings with any existing daemon configuration, then restart Docker (`sudo systemctl restart docker`). The network flags support Docker running inside the development container. `--overlay2=none` makes changes to the container's root filesystem, such as installed packages and `/root/.profile`, survive `docker restart`. Those changes still disappear if the container is removed and recreated; put tools needed by every new container in `Containerfile`. The project directory and named volumes persist separately through their mounts.

# usage
* Start a container for your project directory (it will be mounted read/write):
```bash
python3 /path/to/containerization/codex-container.py ~/projects/example [--name <project-name>]
```

The SSH host and Compose project default to the directory name (`example` above). To choose another name, add `--name my-project`.

The launcher lets Docker choose a free localhost SSH port, starts the container, and adds an SSH host to `~/.ssh/codex-containers.d/`. It also adds one `Include` line to `~/.ssh/config`. The SSH host uses a proxy helper that checks Docker for the current port each time you connect, so a Docker restart does not leave a stale port in SSH config. Run the launcher again after recreating the container to restore the host entry if needed. You need Docker Compose, Python 3, and an `~/.ssh/id_ed25519.pub` key on the host.

If the container exits during startup or has no published SSH port, the launcher reports the failure and leaves the existing SSH config untouched. Check `docker logs` and the container state before recreating it: recreating removes packages and other changes installed directly in the container's root filesystem.

On startup, the entrypoint removes stale `/var/run/docker.pid` and `/var/run/docker/containerd/containerd.pid` before launching the inner Docker daemon. With `--overlay2=none`, these PID files can survive a restart and block the daemon when their process IDs are reused. The container also keeps SSH available if the inner daemon exits, so you can connect and inspect `/var/log/dockerd.log`. These changes apply to containers created from an image rebuilt with the current `entrypoint.py`.

To apply that entrypoint change to an existing stopped container without losing installed tools, copy it into the container before starting it:

```bash
docker cp /path/to/containerization/entrypoint.py lab-search-bot-dev:/usr/local/bin/entrypoint.py
docker start lab-search-bot-dev
python3 /path/to/containerization/codex-container.py /path/to/project
```

Use the matching container and project names for your setup. The launcher refreshes the SSH port after the container starts.

* Install the `ms-vscode.remote-explorer` extension in host VS Code.

* Connect to the SSH host printed by the launcher in Remote Explorer.

* Open codex extention and Sign in via host browser. There's a limitation: at the moment of signing in only one container should be up. Otherwise there's port conflict. So make sure to stop other containers to avoid this.

It's recommended to make a container per each project and use fine-grained personal access tokens with access only to this project repository as your remote git credentials.

Run codex in full access to avoid manually approving permission requests. It *should* be safe as it's containerized and only working directory is mounted. You can check with your terminal what you can access - if you can't reach it, than agent couldnt either (hopefully).

As agent has full access to mounted directory - consider it compromized and don't put any production creds in it.

Running docker inside container is supported, but with out caveat: for networking to work internal containers have to be run with `--networking=host`. It doesn't expose your actual host networking, it uses outer container's network as host network for inner containers.

That means some of compose files won't work as is, and need something like `compose.gvisor.yaml` with network override:
```yaml
services:
  your-service:
    network_mode: host
    networks: !reset []
    ports: !reset []
```

Run docker compose like `docker compose -f compose.yaml -f compose.gvisor.yaml up` to override main compose with gvisor compose.

Another limitation: inner container volumes survive not only outer container restart, but recreation and removing too. To clean them up use `docker volume rm your-service_inner-docker-storage`.
