#!/usr/bin/python
"""Debathena lp wrapper script.

A script that intelligently determines whether a command was intended
for CUPS or LPRng and sends it off in the right direction
"""


import sys

from debathena.printing import common
from debathena.printing import simple


opts = (
    (common.SYSTEM_CUPS, 'EU:cd:h:mn:o:q:st:H:P:i:'),
)


queue_opt = '-d'


def _main(args):
    return simple.simple('lp', opts, queue_opt, args)


def main():
    sys.exit(_main(sys.argv)) # pragma: nocover


if __name__ == '__main__':
    main() # pragma: nocover
