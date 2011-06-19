"""A generator for simple printing utility wrapper scripts.

Given the command line options for the CUPS and LPRng forms of a
command, as well as the specific flag which specifies the print queue
to use, this module generates a main function for a wrapper script
around that command that appropriate dispatches invocations between
the CUPS and LPRng commands.
"""


import os
import sys
import string
import re

from debathena.printing import common


def simple(command, optinfo, queue_opt, args):
    args.pop(0)

    queue = common.get_default_printer()
    try:
        parseresult = common.parse_args(args, optinfo)
        if parseresult == None:
            # Don't barf if neither CUPS nor LPRng syntax was valid (and
            # hence parse_args returns None)
            # Remove this stupidity when we kill LPRng with fire
            print "Syntax Error: Incorrect option passed."
            print "Valid options: " +
                  string.replace(re.sub(r'([a-zA-Z])', r'-\1 ',
                                 optinfo[common.SYSTEM_CUPS][1]), ':', '[arg] ')
            sys.exit(2)
        argstyle, options, arguments = parseresult

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

    args.insert(0, '%s%s' % (queue_opt, queue))
    if server:
        os.environ['CUPS_SERVER'] = server

    common.dispatch_command(system, command, args)
