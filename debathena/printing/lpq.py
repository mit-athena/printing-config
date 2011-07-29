#!/usr/bin/python
"""Debathena lpq wrapper script.

A script that intelligently determines whether a command was intended
for CUPS or LPRng and sends it off in the right direction
"""


import os
import socket
import subprocess
import sys

from debathena.printing import common
from debathena.printing import simple


opts = (
    (common.SYSTEM_CUPS, 'EU:h:P:al'),
    (common.SYSTEM_LPRNG, 'aAlLVcvP:st:D:'),
)


queue_opt = '-P'


def cups_version_is_below_1_4():
    """
    On Debian-based systems, return whether cupsys-bsd is older than 1.4.

    On non-Debian-based systems, return False unconditionally.
    """
    try:
        version = subprocess.Popen(
                      ["dpkg-query", "-W", "-f", "${Version}",
                       "cups-bsd"], stdout=subprocess.PIPE).communicate()[0]
        compare = subprocess.call(
                      ["dpkg", "--compare-versions",
                       version,
                       "lt-nl", "1.4"])
        return compare == 0
    except OSError:
        # Assume the current version of CUPS is fine
        return False

 
def _main(args):
    args.pop(0)

    queue = common.get_default_printer()
    try:
        argstyle, options, arguments = common.parse_args(args, opts)

        # Find the last queue specified in the arguments
        queue_args, options = common.extract_opt(options, queue_opt)
        if queue_args:
            queue = queue_args[-1][-1]

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
                         "No default printer configured. Specify a %s option, or configure a\n"
                         "default printer via e.g. System | Administration | Printing.\n"
                         "\n" % queue_opt))

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

    if system == common.SYSTEM_CUPS and args == []:
        # CUPS clients before 1.4 and CUPS servers at least 1.4 don't
        # communicate well about lpq stuff, so just implement RFC 1179 lpq
        # ourselves since that works
        if cups_version_is_below_1_4():
            try:
                s = socket.socket()
                s.settimeout(10)
                s.connect((server, 515))
                s.send("\x03" + queue + "\n")
                print s.makefile().read()
                return 0
            except (socket.error, socket.timeout):
                # Oh well.
                pass
        
    args.insert(0, '%s%s' % (queue_opt, queue))
    if server:
        os.environ['CUPS_SERVER'] = server

    common.dispatch_command(system, 'lpq', args)


def main():
    sys.exit(_main(sys.argv)) # pragma: nocover


if __name__ == '__main__':
    main() # pragma: nocover
