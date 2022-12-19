import os
import json

ROOT = os.path.dirname(__file__)
BIN = '{}/../bin'.format(ROOT)
DB = '{}/links.json'.format(ROOT)


def save():
    data = []
    for f in os.listdir(BIN):
        real_f = '{}/{}'.format(BIN, f)
        if os.path.islink(real_f):
            t = os.readlink(real_f)
            data.append([f, t])
    data = json.dumps(data)
    open(DB, 'w').write(data)


def restore():
    if os.path.isfile(DB):
        data = json.loads(open(DB, 'r').read())
        for d in data:
            l = '{}/{}'.format(BIN, d[0])
            if not os.path.isfile(l):
                os.symlink(d[1], l)       

        
if __name__ == '__main__':
    save()
