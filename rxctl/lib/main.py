
from .log import LOG
from . import links
from .utils import *

import sys
import os
import subprocess
import getpass
import shlex
from multiprocessing import Pool
from types import SimpleNamespace

from prettytable import PrettyTable
import click

def get_config(ctx, param, value):
    ctx.default_map = get_environment(value, 'config')
    return value

@click.command(
    context_settings=dict(
        ignore_unknown_options = True,
        allow_interspersed_args = False
    ),
)
@click.option(
    '-E', '--environment', 
    default='./environment', 
    show_default=True, 
    help='Script to generate environment (config & inventory)',
    type=click.Path(),
    callback=get_config,
    is_eager=True
)
@click.option('-H', '--host', default=[], help='Comma separated list of host (can be used multiple times)', multiple=True)
@click.option('-S', '--selector', default=[], help='Inventory selector (can be used multiple times)', multiple=True)
@click.option('--use-ssh-password', default=False, is_flag=True, help='Ask for ssh password')
@click.option('--use-sudo-password', default=False, is_flag=True, help='Ask for sudo password')
@click.option('--ssh-opt', default='-o ControlMaster=auto -o ControlPath=/dev/shm/rx-ssh-%h -o ControlPersist=5m -o ConnectTimeout=1', show_default=True, help='SSH options')
@click.option('--password-envvar', default='LC_PASSWD', show_default=True, help='Environment variable used to pass password to sudo')
@click.option('-u', '--user', default=os.environ['USER'], show_default=True, help='SSH user')
@click.option('-P', '--parallel', default=1, show_default=True, help='How many threads to use to run hosts in parallel')
@click.option('-A', '--ad-hoc', default=False, is_flag=True, help='Task list is a remote ad-hoc command')
@click.option('-I', '--inventory', default=False, is_flag=True, help='Show environment inventory')
@click.option('-c', '--check-only', default=False, is_flag=True, help='Show valid inventory')
@click.option('-l', '--task-list', default=False, is_flag=True, help='List tasks in local directory')
@click.option('-t', '--task-help', default=None, help='Show help for a task')
@click.option('-w', '--warning-only', default=False, is_flag=True, help="Don't exit if a host fails check, evict host from inventory")
@click.option('-x', '--exclude', default=[], help='Comma separated list of host to exclude from inventory (can be used multiple times)', multiple=True)
@click.option('-i', '--inline-check', default=False, is_flag=True, help="Don't check hosts before tasks, do it for each host at the begining of the task list")
@click.option('--set-env', default=[], show_default=True, help='Set environment variable (can be used multiple times)', multiple=True)
@click.option('-v', '--verbosity', count=True, default=0, help='Verbosity level, up to 3')
@click.argument('tasks', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def cli(cc, environment, host, selector, use_ssh_password, use_sudo_password, ssh_opt, password_envvar, user, parallel, ad_hoc, inventory, check_only, task_list, task_help, warning_only, exclude, inline_check, set_env, verbosity, tasks):

    # Non-configurable parameters
    remote_shell = '/bin/sh'
    passwd_script = 'rx-passwd'
    passwd_code = '#!/bin/bash\necho "${}"\n'.format(password_envvar)

    # Debug logging
    verbosity = min(verbosity, 3)
    os.environ['RX_LOG_VERBOSITY'] = str(verbosity)
    if verbosity > 0:
        LOG.enable_debug()
        if verbosity > 2:
            ssh_opt = '{} -v'.format(ssh_opt)

    # Restore bin links
    links.restore()
    
    # Debug parameters, actual values 
    for k,v in cc.params.items():
        LOG.debug('{}: {}'.format(k, v))

    # Check arguments - 1
    if (len(selector) == 0 and len(host) == 0) and not (task_list or task_help or inventory):
        LOG.error('At least one of -l, -t, -I, -H, -S or --help must be specified.')
        sys.exit(1)

    # Set path
    basedir = os.path.dirname(os.path.realpath(__file__ + '/..'))
    path = '{}:{}/bin'.format(os.getcwd(),basedir)
    LOG.info('Path: {}:$PATH'.format(path))
    os.environ['PATH'] = '{}:{}'.format(path, os.environ['PATH'])

    # List tasks in current director
    if task_list:
        p = PrettyTable()
        p.field_names = ['Task', 'Description']
        p.align['Task'] = 'r'
        p.align['Description'] = 'l'
        for t in get_tasks():
            p.add_row([click.style(t, fg='blue', bold=True), task_doc(t, short=True)])
        print(p)
        sys.exit()

    # Task help
    if task_help:
        LOG.info('Task help:')
        print()
        print(click.style(task_help, fg='blue', bold=True))
        print(task_doc(task_help))
        sys.exit()

    # Inventory summary
    if inventory and not selector:
        LOG.info('Inventory summary:\n{}'.format(get_environment(environment, 'inventory')))
        sys.exit()

    # Check arguments - 2
    if not (inventory or check_only) and len(tasks) == 0:
        LOG.error('At least one of -I, -c, -A or a task must be specified.')
        sys.exit(1)

    # Build inventory, each host is added only once, first occurence, -H has priority over -S
    INVENTORY = []
    for hlist in host:
        for h in hlist.split(','):
            if not h in INVENTORY:
                INVENTORY.append(h)
    for s in selector:
        host = get_environment(environment, 'inventory', s)
        if host:
            for h in host:
                if not h in INVENTORY:
                    INVENTORY.append(h)
    for xlist in exclude:
        for x in xlist.split(','):
            if x in INVENTORY:
                LOG.debug("Remove '{}' from inventory".format(x))
                INVENTORY.remove(x)
    
    
    # Show inventory
    if inventory:
        LOG.info('Inventory:\n{}'.format(INVENTORY))
        sys.exit()

    # Get password
    passwd = []
    if use_ssh_password:
        passwd.append('SSH')
    if use_sudo_password:
        passwd.append('SUDO')
    if len(passwd) > 0:
        passwd = getpass.getpass('--> {} password : '.format('/'.join(passwd)))

    # Build environment
    os.environ['RX_SHELL'] = remote_shell
    os.environ['RX_BASEDIR'] = basedir
    if parallel > 1:
        os.environ['RX_PARALLEL'] = 'yes'
    os.environ['RX_PASSWD_SCRIPT'] = passwd_script
    os.environ['RX_USER'] = user
    os.environ['RX_PASSWD_ENVVAR'] = password_envvar
    ssh_opt = '{} -o User={}'.format(ssh_opt, user)
    os.environ['RX_SSH_OPT'] = ssh_opt
    ssh_cmd = 'ssh {}'.format(ssh_opt)
    scp_cmd = 'scp {}'.format(ssh_opt)
    if use_ssh_password:
        os.environ['RX_SSH_PASSWORD'] = 'yes'
        os.environ['SSHPASS'] = passwd
        ssh_cmd = 'sshpass -e {}'.format(ssh_cmd)
        scp_cmd = 'sshpass -e {}'.format(scp_cmd)
    os.environ['RX_SSH_CMD'] = ssh_cmd
    os.environ['RX_SCP_CMD'] = scp_cmd
    sudo_cmd = 'sudo -u root'
    if use_sudo_password:
        os.environ['RX_SUDO_PASSWORD'] = 'yes'
        os.environ[password_envvar] = passwd
        sudo_cmd = 'SUDO_ASKPASS=./{} {} -A'.format(passwd_script, sudo_cmd)
    os.environ['RX_SUDO_CMD'] = sudo_cmd
    for ev in set_env:
        ev = ev.split('=')
        os.environ[ev[0].upper()] = ev[1]

    # Context
    ctx = SimpleNamespace()
    ctx.ssh_cmd = ssh_cmd
    ctx.sudo_cmd = sudo_cmd
    ctx.use_sudo_password = use_sudo_password
    ctx.passwd_script = passwd_script
    ctx.passwd_code = passwd_code
    ctx.ad_hoc = ad_hoc
    ctx.parallel = parallel > 1
    ctx.warning_only = warning_only
    ctx.inline_check = inline_check

    # Check hosts
    if check_only or not inline_check: 
        LOG.info('Check hosts connectivity')
        invalid_hosts = []
        with click.progressbar(INVENTORY, bar_template='    [%(bar)s] %(info)s', show_eta=False, item_show_func=lambda x : x) as pbar:
            for h in pbar:
                LOG.set_label(h)
                if verbosity > 0:
                    print()
                valid_host, msg = check(h, ctx)
                if not valid_host:
                    if verbosity == 0:
                        print()
                    if warning_only:
                        LOG.warning(msg)
                    else:
                        LOG.error(msg)
                        sys.exit(1)
                    invalid_hosts.append(h)
                    INVENTORY.remove(h)
        LOG.set_label()
        if len(invalid_hosts) > 0:
            LOG.warning('Remove from inventory:\n{}'.format(invalid_hosts))
        LOG.info('Valid inventory:\n{}'.format(INVENTORY))
    if check_only:
        sys.exit()

    # Build TASK list
    if ad_hoc:
       TASKS = ' '.join(tasks) 
    else:
        TASKS = []
        cmd = {}
        for t in tasks:
            if t.startswith('__'):
                if not check_task(t):
                    LOG.error('Invalid task: {}'.format(t))
                    sys.exit(1)
                if len(cmd) > 0:
                    TASKS.append(cmd)
                cmd = {'name':t, 'args':''}
            else:
                if ' ' in t:
                    cmd['args'] = '{}"{}" '.format(cmd['args'], t)
                else:
                    cmd['args'] = '{}{} '.format(cmd['args'], t)
        if cmd:
            TASKS.append(cmd)
        LOG.info('Task list:\n{}'.format(TASKS))

    worker_parameters = []
    common_parameters = [TASKS, ctx]
    for h in INVENTORY:
             worker_parameters.append([h] + common_parameters)

    if parallel > 1:
        LOG.debug('Parralel processing')
        with Pool(processes=parallel, maxtasksperchild=1) as pool:
            pool.starmap(worker, worker_parameters)
    else:
        for p in worker_parameters:
            worker(*p)


def worker(host, task_list, ctx):
    def run(cmd, label):
        LOG.debug('Worker cmd: {}'.format(cmd))
        if label:
            p = subprocess.Popen(cmd, shell=True, encoding='utf-8', errors='ignore', bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for l in iter(p.stdout.readline,''):
                if l.startswith('['):
                    print(l, end='')
                else:
                    print('[{}] {}'.format(label, l), end='')
            p.wait()
        else:
            p = subprocess.run(cmd, shell=True, encoding='utf-8', errors='ignore', bufsize=0)
        return p.returncode

    os.environ['RX_HOST'] = host
    LOG.set_label(host)
    LOG.info(click.style('START', reverse=True))

    if ctx.parallel:
        llabel = host
    else:
        llabel = None

    if ctx.inline_check:
        LOG.info('Check host connectivity')
        valid_host,msg = check(host, ctx)
        if not valid_host:
            rc = -1
            if ctx.parallel or ctx.warning_only:
                LOG.warning(msg)
            else:
                LOG.error(msg)
                sys.exit(1)
    else:
        valid_host = True

    if valid_host:
        if ctx.ad_hoc:
            LOG.info('Ad-hoc task')
            rc = run("__run '{}'".format(task_list), llabel)
        else:
            for t in task_list:
                rc = run('{} {}'.format(t['name'], t['args']), llabel)
                if rc != 0:
                    break
    
    if rc != 0:
        if ctx.parallel or ctx.warning_only:
            LOG.warning(click.style('Task terminated with error', reverse=True))
        else:
            LOG.error('Task terminated with error, aborting')
            sys.exit(1)
    else:
        LOG.info(click.style('OK', reverse=True))

def check(host, ctx):
    cmd_template = 'set -x ; LOG=$(mktemp -p /tmp rx-XXXXXXXX) ; exec 3>&1 4>&2 1>$LOG 2>&1 ; {} ; RC=$? ; exec 1>&3 2>&4 ; cat $LOG ; rm -fv $LOG ; exit $RC'
    valid_host = True
    cmd = '{} -v {} true'.format(ctx.ssh_cmd, host, host)
    cmd = cmd_template.format(cmd)
    LOG.debug('SSH:\n{}'.format(cmd))
    p = subprocess.run(cmd, shell=True, encoding='utf-8', errors='ignore', bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) #stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if p.returncode != 0:
        valid_host = False
        msg = "Can't do ssh"
    if valid_host and ctx.use_sudo_password:
        cmd = 'cat>{} && chmod 700 {}'.format(ctx.passwd_script, ctx.passwd_script)
        cmd = '{} -v {} /bin/sh -c {}'.format(ctx.ssh_cmd, host, shlex.quote(cmd))
        cmd = cmd_template.format(cmd)
        LOG.debug('Install password script:\n{} | {}'.format(ctx.passwd_code, cmd))
        p = subprocess.run(cmd, shell=True, encoding='utf-8', errors='ignore', bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, input=ctx.passwd_code)
        if p.returncode != 0:
            valid_host = False
            msg = "Can't copy password script"
    if valid_host:
        cmd = '{} -v {} {} true'.format(ctx.ssh_cmd, host , ctx.sudo_cmd)
        cmd = cmd_template.format(cmd)
        LOG.debug('Sudo:\n{}'.format(cmd))
        p = subprocess.run(cmd, shell=True, encoding='utf-8', errors='ignore', bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if p.returncode != 0:
            valid_host = False
            msg = "Can't do sudo"
    if not valid_host:
        msg = '{}: rc={}:\n{}'.format(msg, p.returncode,p.stdout)
    else:
        msg = None
    return valid_host, msg

