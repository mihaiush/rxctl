from .log import LOG

import json
import sys
import subprocess
import glob
import os

import click


def get_environment(env, cmd, selector=''):
    LOG.debug("get_environment: env='{}', cmd='{}', selector='{}'".format(env, cmd, selector))
    if not os.path.isfile(env):
        LOG.warning("'{}' missing".format(env))
        return
    if not os.access(env, os.X_OK):
        LOG.warning("'{}' not executable".format(env))
        return
    if cmd == 'inventory':
        cmd = '{} {}'.format(cmd, selector)
    LOG.info('Get {} from {}'.format(cmd, env))
    p = subprocess.run('{} {}'.format(env, cmd), capture_output=True, shell=True, encoding='utf-8', errors='ignore')
    LOG.debug("get_environment: out:\n{}".format(p.stdout))
    if cmd == 'inventory ':
        data1 = p.stdout.strip()
    else:
        try:
            data1 = json.loads(p.stdout)
        except:
            LOG.error("{} {} didn't return a valid json".format(env, cmd))
            sys.exit(1)
    if cmd == 'config':
        data2 = {}
        for k,v in data1.items():
            data2[k.replace('-','_')] = v
        return data2
    return data1


def check_task(t):
    c = subprocess.run('{} __name__'.format(t), shell=True, encoding='utf-8', errors='ignore', bufsize=0, capture_output=True)
    if c.stdout.strip() == t:
        return True
    return False


def get_tasks():
    tasks = []
    files = glob.glob('__*')
    for f in files:
        if os.path.isfile(f) and os.access(f, os.X_OK):
            if check_task(f):
                LOG.debug('Add task: {}'.format(f))
                tasks.append(f)
            else:
                LOG.debug('Invalid task: {}'.format(f))
    tasks.sort()
    return tasks


def task_doc(task, short=False):
    p = subprocess.run(task, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='ignore')
    if short:
        if p.returncode == 0:
            h = p.stdout.split('\n')
            h = h[0]
        else:
            h = click.style("ERROR, can't get help", fg='red')
    else:
        h = p.stdout
    return h

