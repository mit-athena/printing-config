#!/usr/bin/python
"""Debathena lpr wrapper script.

A script that intelligently determines whether a command was intended
for CUPS or LPRng and sends it off in the right direction
"""


import getopt
import os
import shlex
import sys

from debathena.printing import common


opts = {
    common.SYSTEM_CUPS: 'EH:U:P:#:hlmo:pqrC:J:T:',
}

def _main(args):
    args.pop(0)

    queue = common.get_default_printer()
    argstyle = None
    try:
        # common.SYSTEMS is a canonical order of preference for
        # printing systems, and order matters to common.parse_args
        optinfos = [(s, opts[s]) for s in common.SYSTEMS]

        argstyle, options, arguments = common.parse_args(args, optinfos)

        # Find the last queue specified in the arguments
        queue_args, options = common.extract_opt(options, '-P')
        if queue_args:
            queue = queue_args[-1][-1]

        # Deal with zephyr notifications
        if os.environ.get('ATHENA_USER'):
            system = common.find_queue(queue)[0]
            if system == common.SYSTEM_CUPS:
                options.append(('-m', ''))

        # Now that we've sliced up the arguments, put them back
        # together
        args = [o + a for o, a in options] + arguments
    except ValueError:
        # parse_args returned None, so we learned nothing. We'll just
        # go with the default queue
        pass

    if not queue:
        # We tried and couldn't figure it out, so not our problem
        common.error(2, ("\n"
                         "No default printer configured. Specify a -P option, or configure a\n"
                         "default printer via e.g. System | Administration | Printing.\n"
                         "\n"))

    system, server, queue = common.find_queue(queue)

    if server == None and common.get_cups_uri(queue) == None:
        # if there's no Hesiod server and no local queue, 
        # tell the user they're wrong
        # But let it fall through in case the user is doing 
        # stupid things with -h 
        sys.stderr.write(("\nWARNING: The print queue '%s' does not appear to exist.\n"
                         "If you're trying to print to a cluster or dorm printer,\n"
                         "you should now be using the 'mitprint' queue instead.\n"
                         "See http://mit.edu/printing/pharos for more information.\n\n" % queue))

    args.insert(0, '-P%s' % queue)
    if os.environ.get('ATHENA_USER'):
        args.insert(0, '-U%s' % os.environ['ATHENA_USER'])
    if server:
        os.environ['CUPS_SERVER'] = server

    if system == common.SYSTEM_CUPS and 'LPROPT' in os.environ:
        sys.stderr.write("Use of the $LPROPT environment variable is deprecated and\nits contents will be ignored.\nSee http://kb.mit.edu/confluence/x/awCxAQ\n")

    common.dispatch_command(system, 'lpr', args)


def main():
    sys.exit(_main(sys.argv)) # pragma: nocover


if __name__ == '__main__':
    main() # pragma: nocover
