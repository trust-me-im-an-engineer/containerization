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
  LocalForward 1455 127.0.0.1:1455
```

* Connect to container via installed Remote Explorer extention;

* Open codex extention and Sign in via host browser (that's what LocalForward port is for).