#!/usr/bin/python
"""Test suite for debathena.printing.lpr

These tests are intended to be end-to-end verification of the command
line wrapper scripts. In order to be a faithful end-to-end check, all
test cases should subclass the TestLpr class, and should not stub out
any functions or objects which have not been stubbed out by TestLpr.
"""


import os
import unittest

import cups
import mox

from debathena.printing import common
from debathena.printing import lpr


class TestLpr(mox.MoxTestBase):
    """Tests for the lpr command line wrapper script.

    These tests are intended to be almost perfect end-to-end tests,
    except that they should run consistently in the future in spite of
    a changing environment, Hesiod data, etc.

    In order to maintain the validity of these tests, strict limits
    are placed on what functions and objects can be stubbed out. Those
    stubs are created in this class, to be used in
    subclasses. Subclasses are not allowed to stub out any additional
    functions or objects.

    The functions/objects that have been replaced with mocks are:

      * debathena.printing.common._hesiod_lookup
      * debathena.printing.common.get_cups_uri
      * debathena.printing.common.is_cups_server
      * debathena.printing.common.cupsd
      * os.execvp

    Additionally, while d.p.common.get_direct_printer is not strictly
    at the boundry of Debathena code and the environment, it has been
    stubbed out to avoid pointless boilerplate.

    Finally, os.environ and d.p.common.CUPS_BACKENDS are populated by
    the environ and backends (respectively) attributes of the test
    class.
    """
    environ = {}
    backends = []

    def setUp(self):
        super(TestLpr, self).setUp()

        self.mox.stubs.Set(os, 'environ', self.environ)
        self.mox.stubs.Set(common, 'CUPS_BACKENDS', self.backends)
        self.mox.stubs.Set(common, 'cupsd', self.mox.CreateMock(cups.Connection))
        self.mox.stubs.Set(common, '_loaded', True)

        self.mox.StubOutWithMock(common, '_hesiod_lookup')
        self.mox.StubOutWithMock(common, 'get_cups_uri')
        self.mox.StubOutWithMock(common, 'is_cups_server')
        self.mox.StubOutWithMock(common, 'get_default_printer')
        self.mox.StubOutWithMock(os, 'execvp')


class TestNonexistantPrinter(TestLpr):
    # LPROPT, PRINTER are unset
    environ = {'ATHENA_USER': 'quentin'}

    def test(self):
        """Test printing to a printer that is not in Hesiod.

        Taken from -c debathena, reported by quentin on May 14, 2010."""
        common._hesiod_lookup('stark', 'pcap').AndReturn([])
        common.get_default_printer().AndReturn(None)
        common.get_cups_uri('stark').AndReturn(None)

        # Result:
        os.execvp('cups-lpr', ['lpr', '-Uquentin', '-Pstark', '-m', 'puppies biting nose.jpg'])

        self.mox.ReplayAll()

        lpr._main(['lpr', '-Pstark', 'puppies biting nose.jpg'])


class TestLpropt(TestLpr):
    environ = {'ATHENA_USER': 'jdreed', 'LPROPT': '-Zduplex'}
    backends = ['get-print.mit.edu']

    def test(self):
        """Test printing with LPROPT set.

        Taken from Trac #509, reported on Mar 12, 2010."""
        common._hesiod_lookup('ajax', 'pcap').AndReturn(['ajax:rp=ajax:rm=GET-PRINT.MIT.EDU:ka#0:mc#0:'])
        common.get_default_printer().AndReturn(None)
        common.get_cups_uri('ajax').AndReturn(None)
        common.is_cups_server('GET-PRINT.MIT.EDU').AndReturn(True)

        # Result:
        os.execvp('cups-lpr', ['lpr', '-Ujdreed', '-Pajax', '-osides=two-sided-long-edge', '-m'])

        self.mox.ReplayAll()

        lpr._main(['lpr', '-P', 'ajax'])


class TestNoLpropt(TestLpr):
    environ = {'ATHENA_USER': 'jdreed'}
    backends = ['get-print.mit.edu']

    def test(self):
        """Test printing with LPROPT unset.

        Taken from Trac #509, reported on Mar 12, 2010."""
        common._hesiod_lookup('ajax', 'pcap').AndReturn(['ajax:rp=ajax:rm=GET-PRINT.MIT.EDU:ka#0:mc#0:'])
        common.get_default_printer().AndReturn(None)
        common.get_cups_uri('ajax').AndReturn(None)
        common.is_cups_server('GET-PRINT.MIT.EDU').AndReturn(True)

        # Result:
        os.execvp('cups-lpr', ['lpr', '-Ujdreed', '-Pajax', '-m'])

        self.mox.ReplayAll()

        lpr._main(['lpr', '-P', 'ajax'])


if __name__ == '__main__':
    unittest.main()
