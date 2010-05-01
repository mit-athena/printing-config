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

    def test_local_mdns_queue(self):
        """Verify that find_queue doesn't interfere with truly local printers."""
        printing.get_cups_uri('foo').AndReturn('dnssd://patience._printer._tcp.local.')

        self.mox.ReplayAll()

        self.assertEqual(printing.find_queue('foo'),
                         (printing.SYSTEM_CUPS, None, 'foo'))


if __name__ == '__main__':
    unittest.main()
