#!/usr/bin/env python3

import logging
import sys
import click
import os

class CustomFormatter(logging.Formatter):

    colors = {
        logging.NOTSET: 'reset',
        logging.DEBUG: 'cyan',
        logging.INFO: 'green',
        logging.WARNING: 'yellow',
        logging.ERROR: 'red',
        logging.CRITICAL: 'red'
    }

    
    level = logging.INFO
    prompt = '-->'

    def set_label(self, label):
        if label:
            self.label = label
        else:
            self.label = self.prompt

    def format(self, record):
        c = self.colors[record.levelno]

        # Split msg in first line msg0, and the rest of the text msg1
        msg = record.msg.split('\n')
        msg0 = msg[0]
        if len(msg) > 1:
            msg1 = '\n{}'.format('\n'.join(msg[1:]))
        else:
            msg1 = ''
        # Colorize only first line off message
        record.msg = '{}{}'.format(click.style(msg0, fg=c), msg1)
        
        # Timestamp if debug enabled
        if self.level == logging.DEBUG:
            ts = click.style(' %(asctime)s', fg=c)
        else:
            ts = ''

        level = click.style('%(levelname)s', fg=c, bold=True)
        if self.label.endswith(self.prompt):
            label = self.label
        else:
            label = '[{}]'.format(click.style(self.label, fg=c))
        
        log_fmt = '{}{} {}: %(message)s'.format(label, ts, level)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class Logger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.setLevel(logging.INFO)
        self.fmt = CustomFormatter()
        lh = logging.StreamHandler(sys.stderr)
        lh.setFormatter(self.fmt)
        self.addHandler(lh)

    def enable_debug(self, e=True):
        if e:
            self.setLevel(logging.DEBUG)
        else:
            self.setLevel(logging.INFO)
        self.fmt.level = self.level

    def set_label(self, label=None):
        self.fmt.set_label(label)

logging.setLoggerClass(Logger)
LOG = logging.getLogger(__name__)

if 'RX_LOG_VERBOSITY' in os.environ and int(os.environ['RX_LOG_VERBOSITY']) > 0:
    LOG.enable_debug()

if 'RX_HOST' in os.environ:
    label = os.environ['RX_HOST']
    if 'RX_TASK' in os.environ:
        label = '{}/{}'.format(os.environ['RX_HOST'], os.environ['RX_TASK'])
else:
    label = None
LOG.set_label(label)


if __name__ == '__main__':

    levelmap = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR
    }

    level = os.path.basename(__file__).split('.')
    if len(sys.argv) >= 2 and level[-1] in levelmap:
        level = level[-1]
        msg = ' '.join(sys.argv[1:])
    elif len(sys.argv) >= 3 and sys.argv[1] in levelmap:
        level = sys.argv[1]
        msg = ' '.join(sys.argv[2:])
    else:
        print('{} {} message'.format(os.path.basename(__file__), '|'.join(levelmap.keys()))) 
        sys.exit(2)

    LOG.log(levelmap[level], msg)

    if level == 'error':
        sys.exit(1)
 
