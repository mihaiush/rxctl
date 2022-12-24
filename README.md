# rxctl
Linux remote execution tool.
## What is rxctl ?
It executes tasks (scripts) on remote hosts over SSH and SUDO. The tasks can contain remote and local executed code. Remote code is always executed as root, sudo is used to elevate privileges. It is heavily influenced by fabric (https://www.fabfile.org) and cdis (https://www.cdi.st/manual/latest/index.html):
- tasks and helper tools names start with __,
- tasks are written in shell script (/bin/sh),
- it is not a configuration tool but a scripting one. It doesn’t try to achieve any kind of idempotency, commands are executed in order they appear in task,  

The tool itself is not involved in the remote code execution in any way, its job is to prepare a list of hosts and an environment in which external scripts (tasks) are executed on each host (sequential or in parallel). The remote execution is handled by some helper commands (__run, __get, __put, …) 
