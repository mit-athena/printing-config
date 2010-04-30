"""Debathena printing configuration"""


import getopt
import os
import socket
import urllib

import cups
import hesiod


_loaded = False
CUPS_FRONTENDS = [
    'printers.mit.edu',
    'cluster-printer.mit.edu',
    'cups.mit.edu',
    ]
CUPS_BACKENDS = []
cupsd = None


SYSTEM_CUPS = 0
SYSTEM_LPRNG = 1
SYSTEMS = [SYSTEM_CUPS, SYSTEM_LPRNG]


def _hesiod_lookup(hes_name, hes_type):
    """A wrapper with somewhat graceful error handling."""
    try:
        h = hesiod.Lookup(hes_name, hes_type)
        if len(h.results) > 0:
            return h.results
    except IOError:
        return []


def _setup():
    global _loaded
    if not _loaded:
        CUPS_BACKENDS = [s.lower() for s in
                         _hesiod_lookup('cups-print', 'sloc') +
                         _hesiod_lookup('cups-cluster', 'sloc')]
        try:
            cupsd = cups.Connection()
        except RuntimeError:
            pass

        _loaded = True


def get_cups_uri(printer):
    _setup()
    if cupsd:
        try:
            attrs = cupsd.getPrinterAttributes(printer)
            return attrs.get('device-uri')
        except cups.IPPError:
            pass


def parse_args(args, optinfos):
    """Parse an argument list, given multiple ways to parse it.

    The Debathena printing wrapper scripts sometimes have to support
    multiple, independent argument sets from the different printing
    systems' versions of commands.

    parse_args tries to parse arguments with a series of different
    argument specifiers, returning the first parse that succeeds.

    The optinfos argument provides information about the various ways
    to parse the arguments, including the order in which to attempt
    the parses. optinfos should be a list of 2-tuples of the form
    (opt_identifier, optinfo).

    The opt_identifier from the first tuple that successfully parses
    is included as part of the return value. optinfo is a list of
    short options in the same format as getopt().

    Args:
      args: The argv-style argument list to parse
      optinfos: A list of 2-tuples of the form (opt_identifier,
        optinfo).

    Returns:
      A tuple of (opt_identifier, options, arguments), where options
      and arguments are returned by the first run of getopt that
      succeeds.
    """

    for opt_identifier, optinfo in optinfos:
      try:
          options, arguments = getopt.gnu_getopt(args, optinfo)
          return opt_identifier, options, arguments
      except getopt.GetoptError:
          # That version doesn't work, so try the next one
          continue


def extract_opt(options, optname):
    """Finds a particular argument and removes it.

    Useful when you want to find a particular argument, extract_opt
    looks through a list of options in the format getopt returns
    them. It finds all instances of optnames and extracts them.

    Args:
      options: A list of options as returned from getopt (i.e. [('-P',
        'barbar')])
      optname: The option to extract. The option should have an
        opening dash (i.e. '-P')

    Returns:
      A tuple of (extracted, remaining), where extracted is the list
      of arguments that matched optname, and remaining is the list of
      arguments that don't
    """
    extracted = []
    remaining = []
    for o, v in options:
        if o == optname:
            extracted.append((o, v))
        else:
            remaining.append((o, v))
    return extracted, remaining


def get_default_printer():
    """Find and return the default printer"""
    _setup()

    if 'PRINTER' in os.environ:
        return os.environ['PRINTER']

    if cupsd:
        default = cups.getDefault()
        if default:
            return default

    for result in _hesiod_lookup(socket.getfqdn(), 'cluster'):
        key, value = result.split(None, 1)
        if key == 'lpr':
            return value


def find_queue(queue):
    """Figure out which printing system to use for a given printer

    This function makes a best effort to figure out which server and
    which printing system should be used for printing to queue.

    If a specified queue appears to be an Athena print queue, we use
    Hesiod to determine the print server. If the print server in
    Hesiod accepts connections on port 631, we conclude that jobs
    should be sent to that server over CUPS. Otherwise, we assume
    LPRng.

    A queue is assumed to be an Athena print queue if it's not
    configured in the default CUPS server. It's also assumed to be an
    Athena print queue if the default CUPS server simply bounces jobs
    to any of the Athena print servers.

    If a queue is not an Athena print queue, then we always use the
    default CUPS server.

    Note that users might configure a local print queue pointing to an
    Athena print queue with a different name from the Athena print
    queue (i.e. have a w20 queue that bounces jobs to the ajax Athena
    queue). In that scenario, we still want to send the job directly
    to the Athena print server, but we also need to translate the
    name. Therefore, find_queue includes the translated queue name in
    its return values.

    Args:
      queue: The name of a print queue

    Returns:
      A tuple of (printing_system, print_server, queue_name)

      printing_system is one of the PRINT_* constants in this module
    """
    _setup()
    url = get_cups_uri(queue)
    if url:
        proto = rest = hostport = path = host = port = None

        (proto, rest) = urllib.splittype(url)
        if rest:
            (hostport, path) = urllib.splithost(rest)
        if hostport:
            (host, port) = urllib.splitport(hostport)
        if (proto and host and path and
            proto == 'ipp' and
            host.lower() in CUPS_FRONTENDS + CUPS_BACKENDS):
            # Canonicalize the queue name to Athena's, in case someone
            # has a local printer called something memorable like 'w20'
            # that points to 'ajax' or something
            if path[0:10] == '/printers/':
                queue = path[10:]
            elif path[0:9] == '/classes/':
                queue = path[9:]
            else: # we can't parse CUPS' URL, punt to CUPS
                return SYSTEM_CUPS, None, queue
        else:
            return SYSTEM_CUPS, None, queue

    # Get rid of any instance on the queue name
    # TODO The purpose of instances is to have different sets of default
    # options. Queues may also have default options on the null
    # instance. Figure out if we need to do anything about them
    queue = queue.split('/')[0]

    # If we're still here, the queue is definitely an Athena print
    # queue; it was either in the local cupsd pointing to Athena, or the
    # local cupsd didn't know about it.
    # Figure out what Athena thinks the backend server is, and whether
    # that server is running a cupsd; if not, fall back to LPRng

    pcap = _hesiod_lookup(queue, 'pcap')
    rm = None
    if pcap:
        for field in pcap[0].split(':'):
            if field[0:3] == 'rm=':
                rm = field[3:]
    if not rm:
        # In the unlikely event we're wrong about it being an Athena
        # print queue, the local cupsd is good enough
        return SYSTEM_CUPS, None, queue

    try:
        # See if rm is running a cupsd. If not, assume it's an LPRng server.
        s = socket.socket()
        s.settimeout(0.3)
        s.connect((rm, 631))
        s.close()

        return SYSTEM_CUPS, rm, queue
    except (socket.error, socket.timeout):
        return SYSTEM_LPRNG, rm, queue


__all__ = ['SYSTEM_CUPS', 'SYSTEM_LPRNG', 'SYSTEMS'
           'get_cups_uri',
           'parse_args',
           'extract_opt',
           'get_default_printer',
           'find_queue',
           ]
