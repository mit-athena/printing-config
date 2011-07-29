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
    common.SYSTEM_LPRNG: 'ABblC:D:F:Ghi:kJ:K:#:m:NP:rR:sT:U:Vw:X:YZ:z1:2:3:4:',
}


def translate_lprng_args_to_cups(args):
    # TODO yell at user if/when we decide that these args are deprecated

    # If getopt fails, something went very wrong -- _we_ generated this
    options, realargs = getopt.gnu_getopt(args, opts[common.SYSTEM_LPRNG])
    cupsargs = []
    for (o, a) in options:
        if o in ('-b', '-l'):
            cupsargs += [('-l', a)]
        elif o in ('-h'):
            cupsargs += [('-h', a)]
        elif o in ('-J'):
            cupsargs += [('-J', a)]
        elif o in ('-K', '-#'):
            cupsargs += [('-#', a)]
        elif o in ('-P'):
            cupsargs += [('-P', a)]
        elif o in ('-T'):
            cupsargs += [('-T', a)]
        elif o in ('-U'):
            cupsargs += [('-U', a)]
        elif o in ('-Z'):
            if a == 'simplex':
                cupsargs += [('-o', 'sides=one-sided')]
            elif a == 'duplex':
                cupsargs += [('-o', 'sides=two-sided-long-edge')]
            elif a == 'duplexshort':
                cupsargs += [('-o', 'sides=two-sided-short-edge')]
            # TODO attempt to deal banner=staff
        elif o in ('-m'):
            # Intentionally drop any argument to -m; zephyrs always go
            # to you
            cupsargs += [('-m', '')]
        else:
            sys.stderr.write("Warning: option %s%s not converted to CUPS\n"
                             % (o, a))
    joincupsargs = [o + a for o, a in cupsargs] + realargs
    return joincupsargs


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
        zephyr_args, options = common.extract_opt(options, '-N')
        if not zephyr_args and os.environ.get('ATHENA_USER'):
            system = common.find_queue(queue)[0]
            if argstyle == common.SYSTEM_LPRNG:
                options.append(('-m', 'zephyr%' + os.environ['ATHENA_USER']))
            elif system == common.SYSTEM_CUPS:
                options.append(('-m', ''))
            elif system == common.SYSTEM_LPRNG:
                options.append(('-m', 'zephyr%' + os.environ['ATHENA_USER']))

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
    if system == common.SYSTEM_CUPS and argstyle == common.SYSTEM_LPRNG:
        args = translate_lprng_args_to_cups(args)

    if system == common.SYSTEM_CUPS and 'LPROPT' in os.environ:
        sys.stderr.write("Use of the $LPROPT environment variable is deprecated and\nits contents will be ignored.\nSee http://kb.mit.edu/confluence/x/awCxAQ\n")

    common.dispatch_command(system, 'lpr', args)


def main():
    sys.exit(_main(sys.argv)) # pragma: nocover


if __name__ == '__main__':
    main() # pragma: nocover
