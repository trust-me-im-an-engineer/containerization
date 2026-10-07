This simple container setup isolates codex from your host system. It does so by creating an unprivileged container with openssh-server. Connect your host vscode to the container via ssh to get a near-native development experience with isolation safety.

# usage
* Create container:
```bash
SSH_PORT=<some free host port> podman compose --file <path to containerization>/compose.yml -p <container name> up -d
```

* Install `ms-vscode.remote-explorer` extension on host vscode;

* Add ssh entry to ~/.ssh/config:
```
Host <container-name>
  HostName 127.0.0.1
  Port <host port you used as SSH_PORT>
  User root
```

* Connect to container via installed Remote Explorer extention;

* Open codex extention and Sign in via host browser. There's a limitation: at the moment of signing in only one container should be up. Otherwise there's port conflict. So make sure to stop other containers to avoid this.

It's recommended to make a container per each project and use fine-grained personal access tokens with access only to this project repository as your remote git credentials.

Run codex in full access to avoid manually approving permission requests. It *should* be safe as it's containerized and only working directory is mounted. You can check with your terminal what you can access - if you can't reach it, than agent couldnt either (hopefully).

As agent has full access to mounted directory - consider it compromized and don't put any production creds in it.