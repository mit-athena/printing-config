#!/usr/bin/python
"""Test suite for debathena.printing"""


import unittest

import cups
import hesiod
import mox

from debathena import printing


class TestHesiodLookup(mox.MoxTestBase):
    def setUp(self):
        super(TestHesiodLookup, self).setUp()

        self.mox.StubOutWithMock(hesiod, 'Lookup')

    def test_valid(self):
        """Test _hesiod_lookup on a record that exists"""
        class FakeResults(object): pass
        h = FakeResults()
        h.results = ['ajax:rp=ajax:rm=GET-PRINT.MIT.EDU:ka#0:mc#0:']

        hesiod.Lookup('ajax', 'pcap').AndReturn(h)

        self.mox.ReplayAll()

        self.assertEqual(printing._hesiod_lookup('ajax', 'pcap'),
                         h.results)

    def test_enoent(self):
        """Test _hesiod_lookup on nonexistent record"""
        hesiod.Lookup('doesnt_exist', 'pcap').AndRaise(
            IOError(2, 'No such file or directory'))

        self.mox.ReplayAll()

        self.assertEqual(printing._hesiod_lookup('doesnt_exist', 'pcap'),
                         [])


class TestCanonicalizeQueue(mox.MoxTestBase):
    def setUp(self):
        super(TestCanonicalizeQueue, self).setUp()

        def _setup_side_effects():
            printing.CUPS_FRONTENDS = ['printers.mit.edu', 'cluster-printers.mit.edu']
            printing.CUPS_BACKENDS = ['get-print.mit.edu']
        self.mox.StubOutWithMock(printing, '_setup')
        printing._setup().WithSideEffects(_setup_side_effects)

        self.mox.StubOutWithMock(printing, 'get_cups_uri')

    def test_non_local_queue(self):
        """Test canonicalize_queue with a non-local queue name"""
        printing.get_cups_uri('python').AndReturn(None)
        self.mox.ReplayAll()
        self.assertEqual(printing.canonicalize_queue('python'),
                         'python')

    def test_local_only_name(self):
        """Test canonicalize_queue on a local-only queue"""
        printing.get_cups_uri('patience').AndReturn('mdns://patience._printer._tcp.local.')
        self.mox.ReplayAll()
        self.assertEqual(printing.canonicalize_queue('patience'),
                         None)

    def test_invalid_queue_uri(self):
        """Test canonicalize_queue with a URL we don't understand"""
        printing.get_cups_uri('screwedup').AndReturn('ipp://PRINTERS.MIT.EDU/stuff/screwedup')
        self.mox.ReplayAll()
        self.assertEqual(printing.canonicalize_queue('screwedup'),
                         None)

    def test_valid_printer(self):
        """Test a locally configured bounce to an Athena printer"""
        printing.get_cups_uri('ajax').AndReturn('ipp://cluster-printers.mit.edu:631/printers/ajax')
        self.mox.ReplayAll()
        self.assertEqual(printing.canonicalize_queue('ajax'),
                         'ajax')

    def test_misnamed_valid_printer(self):
        """Test a local bounce queue with a different name from the Athena queue"""
        printing.get_cups_uri('w20').AndReturn('ipp://cluster-printers.mit.edu:631/printers/ajax')
        self.mox.ReplayAll()
        self.assertEqual(printing.canonicalize_queue('w20'),
                         'ajax')

    def test_valid_class(self):
        """Test a locally configured bounce queue to an Athena class"""
        printing.get_cups_uri('ajax2').AndReturn('ipp://cluster-printers.mit.edu:631/classes/ajax2')
        self.mox.ReplayAll()
        self.assertEqual(printing.canonicalize_queue('ajax2'),
                         'ajax2')


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
