This container setup isolates codex from your host system. It does so by creating docker container with gvisor isolation and openssh-server inside. Connect your host vscode to the container via ssh to get a near-native development experience with isolation safety.

# usage
* Start a container for your project directory (it will be mounted read/write):
```bash
python3 /path/to/containerization/codex-container.py ~/projects/example [--name <project-name>]
```

The SSH host and Compose project default to the directory name (`example` above). To choose another name, add `--name my-project`.

The launcher lets Docker choose a free localhost SSH port, starts the container, and adds an SSH host to `~/.ssh/codex-containers.d/`. It also adds one `Include` line to `~/.ssh/config`. Run the same command again after restarting or recreating the container to refresh its port. You need Docker Compose, Python 3, and an `~/.ssh/id_ed25519.pub` key on the host.

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
