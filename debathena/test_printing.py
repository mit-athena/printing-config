#!/usr/bin/python
"""Test suite for debathena.printing"""


import unittest

import cups
import mox

from debathena import printing


class TestFindQueue(mox.MoxTestBase):
    def setUp(self):
        super(TestFindQueue, self).setUp()

        self.mox.StubOutWithMock(printing, 'canonicalize_queue')
        self.mox.StubOutWithMock(printing, 'get_hesiod_print_server')
        self.mox.StubOutWithMock(printing, 'is_cups_server')

    def test_local_mdns_queue(self):
        """Verify that find_queue doesn't interfere with truly local printers."""
        printing.canonicalize_queue('foo').AndReturn(None)

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('foo'),
                         (printing.SYSTEM_CUPS, None, 'foo'))

    def test_athena_cups_queue(self):
        """Verify that find_queue can find non-local Athena queues on CUPS"""
        printing.canonicalize_queue('ajax').AndReturn('ajax')
        printing.get_hesiod_print_server('ajax').AndReturn('GET-PRINT.MIT.EDU')
        printing.is_cups_server('GET-PRINT.MIT.EDU').AndReturn(True)

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('ajax'),
                         (printing.SYSTEM_CUPS, 'GET-PRINT.MIT.EDU', 'ajax'))

    def test_athena_lprng_queue(self):
        """Verify that find_queue can find non-local Athena queues on LPRng"""
        printing.canonicalize_queue('ashdown').AndReturn('ashdown')
        printing.get_hesiod_print_server('ashdown').AndReturn('MULCH.MIT.EDU')
        printing.is_cups_server('MULCH.MIT.EDU').AndReturn(False)

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('ashdown'),
                         (printing.SYSTEM_LPRNG, 'MULCH.MIT.EDU', 'ashdown'))

    def test_misnamed_local_queue(self):
        """Verify that find_queue will use canonicalized queue names"""
        printing.canonicalize_queue('w20').AndReturn('ajax')
        printing.get_hesiod_print_server('ajax').AndReturn('GET-PRINT.MIT.EDU')
        printing.is_cups_server('GET-PRINT.MIT.EDU').AndReturn(True)

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('w20'),
                         (printing.SYSTEM_CUPS, 'GET-PRINT.MIT.EDU', 'ajax'))

    def test_queue_with_instance(self):
        """Verify that find_queue will strip instances"""
        printing.canonicalize_queue('ajax/2sided').AndReturn('ajax/2sided')
        printing.get_hesiod_print_server('ajax').AndReturn('GET-PRINT.MIT.EDU')
        printing.is_cups_server('GET-PRINT.MIT.EDU').AndReturn(True)

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('ajax/2sided'),
                         (printing.SYSTEM_CUPS, 'GET-PRINT.MIT.EDU', 'ajax'))


if __name__ == '__main__':
    unittest.main()
