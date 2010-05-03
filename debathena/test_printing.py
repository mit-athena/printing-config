#!/usr/bin/python
"""Test suite for debathena.printing"""


import unittest

import cups
import mox

from debathena import printing


class TestFindQueue(mox.MoxTestBase):
    def setUp(self):
        super(TestFindQueue, self).setUp()

        def _setup_side_effects():
            printing.CUPS_BACKENDS = ['get-print.mit.edu']
        self.mox.StubOutWithMock(printing, '_setup')
        printing._setup().WithSideEffects(_setup_side_effects)

        self.mox.StubOutWithMock(printing, 'get_cups_uri')
        self.mox.StubOutWithMock(printing, 'get_hesiod_print_server')
        self.mox.StubOutWithMock(printing, 'is_cups_server')

    def test_local_mdns_queue(self):
        """Verify that find_queue doesn't interfere with truly local printers."""
        printing.get_cups_uri('foo').AndReturn('dnssd://patience._printer._tcp.local.')

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('foo'),
                         (printing.SYSTEM_CUPS, None, 'foo'))

    def test_athena_cups_queue(self):
        """Verify that find_queue can find non-local Athena queues on CUPS"""
        printing.get_cups_uri('ajax').AndReturn(None)
        printing.get_hesiod_print_server('ajax').AndReturn('GET-PRINT.MIT.EDU')
        printing.is_cups_server('GET-PRINT.MIT.EDU').AndReturn(True)

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('ajax'),
                         (printing.SYSTEM_CUPS, 'GET-PRINT.MIT.EDU', 'ajax'))

    def test_athena_lprng_queue(self):
        """Verify that find_queue can find non-local Athena queues on LPRng"""
        printing.get_cups_uri('ashdown').AndReturn(None)
        printing.get_hesiod_print_server('ashdown').AndReturn('MULCH.MIT.EDU')
        printing.is_cups_server('MULCH.MIT.EDU').AndReturn(False)

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('ashdown'),
                         (printing.SYSTEM_LPRNG, 'MULCH.MIT.EDU', 'ashdown'))


if __name__ == '__main__':
    unittest.main()
