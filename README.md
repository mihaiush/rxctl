# rxctl
Linux remote execution tool.

## What is rxctl ?
It executes tasks (scripts) on remote hosts over SSH and SUDO. The tasks can contain remote and local executed code. Remote code is always executed as root, sudo is used to elevate privileges. It may work on other UNIX-like OS but it was only tested on Linux (Debian) and it relies on /bin/bash for most of its helper tools. It is heavily influenced by fabric (https://www.fabfile.org) and cdis (https://www.cdi.st/manual/latest/index.html):
- tasks and helper tools names start with __,
- tasks are written in shell script (/bin/sh),
- it is not a configuration tool but a scripting one. It doesn’t try to achieve any kind of idempotency, commands are executed in order they appear in task,  

The tool itself is not involved in the remote code execution in any way, its job is to prepare a list of hosts and an environment in which external scripts (tasks) are executed on each host (sequential or in parallel). The remote execution is handled by some helper commands (__run, __get, __put, …). It also adds the current directory and the bin directory to the path. 

```
rxctl [OPTIONS] [TASKS]...

Options:
  -E, --environment PATH  Script to generate environment (config & inventory)
                          [default: ./environment]
  -H, --host TEXT         Comma separated list of host (can be used multiple
                          times)
  -S, --selector TEXT     Inventory selector (can be used multiple times)
  --use-ssh-password      Ask for ssh password
  --use-sudo-password     Ask for sudo password
  --ssh-opt TEXT          SSH options  [default: -o ControlMaster=auto -o
                          ControlPath=/dev/shm/rx-ssh-%h -o ControlPersist=5m
                          -o ConnectTimeout=1]
  --password-envvar TEXT  Environment variable used to pass password to sudo
                          [default: LC_PASSWD]
  -u, --user TEXT         SSH user  [default: current user]
  -P, --parallel INTEGER  How many threads to use to run hosts in parallel
                          [default: 1]
  -A, --ad-hoc            Task list is a remote ad-hoc command
  -I, --inventory         Show environment inventory
  -c, --check-only        Show valid inventory
  -l, --task-list         List tasks in local directory
  -t, --task-help TEXT    Show help for a task
  -w, --warning-only      Don't exit if a host fails check, evict host from
                          inventory
  -x, --exclude TEXT      Comma separated list of host to exclude from
                          inventory (can be used multiple times)
  --set-env TEXT          Set environment variable (can be used multiple
                          times)
  -v, --verbosity         Verbosity level, up to 3
  --help                  Show this message and exit.
```

## Environment script
The environment script (default ```./environment```) is used to overwrite rxctl parameters and to generate the list of host (inventory) on which to run the tasks:
- ```environment check```, should produce a JSON dictionary of parameters you want to overwrite,
- ```environment inventory```, free text which is displayed when you run ```rxctl -I``` without any other parameter,
- ```environment inventory <SELECTOR>```, JSON list of hosts

## Helper tools
### __init
### __run
### __get, __put
### __log
### __wait
### __ansible
