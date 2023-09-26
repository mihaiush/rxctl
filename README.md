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
  -u, --user TEXT         SSH user  [default: ***]
  -P, --parallel          Run hosts in parallel
  --max-parallel INTEGER  How many threads to use to run hosts in parallel, 0
                          - run everything in parralel  [default: 0]
  -A, --ad-hoc            Task list is a remote ad-hoc command
  -I, --inventory         With -S shows the list of hosts, by itself shows the
                          inventory summary.
  -c, --check-only        Show valid inventory
  -l, --task-list         List tasks in local directory
  -t, --task-help TEXT    Show help for a task
  -w, --warning-only      Don't exit if a host fails check, evict host from
                          inventory
  -x, --exclude TEXT      Comma separated list of host to exclude from
                          inventory (can be used multiple times)
  -i, --inline-check      Don't check hosts before tasks, do it for each host
                          at the begining of the task list
  --set-env TEXT          Set environment variable (can be used multiple
                          times)
  -v, --verbosity         Verbosity level, up to 3
  -V, --version           Show the version and exit.
  --help                  Show this message and exit.
```

## Environment script
The environment script (default ```./environment```) is used to overwrite rxctl parameters and to generate the list of host (inventory) on which to run the tasks:
- ```environment check```, should produce a JSON dictionary of parameters you want to overwrite,
- ```environment inventory```, free text which is displayed when you run ```rxctl -I``` without any other parameter,
- ```environment inventory <SELECTOR>```, JSON list of hosts

## Helper tools
### __init
Makes an arbitrary script a task
```
. __init <<EOF
Short help (rxctl -l)

Long help (rxctl -t TASK)
EOF
```
### __run
Run a remote command
```
__run 'COMMAND1 ; COMMAND2 ; ...'
```
or
```
__run <<EOF
COMMAND1
COMMAND2
EOF
```
### __get, __put
Copy files from/to remote host
### __log
Log message
```
__log.LEVEL MESSAGE
```
### __wait
Wait for an event to happen
```
__wait ACTION CHECK TIMEOUT STEP DELAY
ACTION - a label to display in log messages
CHECK - command executed to check the status, if rc 0 exit wait
TIMEOUT - max wait in seconds
STEP - interval to run check
DELAY - initial delay
```
### __ansible
Run ansible module.
It requires ansible, instalation directoty should be passed to rxctl with *set-env*, e.g.:
```
rxctl --set-env RX_ANSIBLE=/usr/lib/python3/dist-packages/ansible
```
Invocation:
```
__ansible MODULE [--PARAM1=VAL1] [--PARAM2=VAL2]
```
or
```
__ansible.package [PACKAGE_NAME] [--PARAM1=VAL1] [--PARAM2=VAL2]
__ansible.service [SERVICE_NAME] [--PARAM1=VAL1] [--PARAM2=VAL2]
__ansible.setup [SUBSET] [--PARAM1=VAL1] [--PARAM2=VAL2]
```
or return one fact from subset *distribution,pkg_mgr,service_mgr,virtual*:
```
__ansible.fact FACT
```
