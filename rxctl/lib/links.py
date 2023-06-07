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
    with open(DB, 'w') as f:
        f.write(data)


def restore():
    if os.path.isfile(DB):
        with open(DB, 'r') as f:
            data = json.loads(f.read())
        for d in data:
            lnk = '{}/{}'.format(BIN, d[0])
            if not os.path.isfile(lnk):
                os.symlink(d[1], lnk)


if __name__ == '__main__':
    save()
