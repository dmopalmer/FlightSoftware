import unittest
import logging
from ax5043_manager import Manager
from mock_ax5043_driver import MockAx5043
from ax5043_driver import Reg, Bits

class TestManager(unittest.TestCase):
    def test_autorange_slow_xtal(self):
        mock = MockAx5043()
        mgr = Manager(mock)
        mgr.dispatch()
        self.assertTrue(isinstance(mgr.state, Manager.Autoranging))
        mock.read_queue[Reg.XTALSTATUS] = Bits.XTAL_RUN
        mgr.dispatch()
        self.assertFalse(mgr.is_faulted())

    def test_tx(self):
        mock = MockAx5043()
        mock.read_defaults[Reg.XTALSTATUS] = Bits.XTAL_RUN
        mock.read_defaults[Reg.POWSTAT] |= Bits.SVMODEM
        mgr = Manager(mock)
        # Transition to autoranging
        mgr.dispatch()
        # Transition to idle
        mgr.dispatch()
        # Stay in idle when tx_enabled=False
        mgr.inbox.put(bytearray([0xCA, 0xFE, 0xBA, 0xBE]))
        mgr.dispatch()
        self.assertTrue(isinstance(mgr.state, Manager.Idle))
        # Transition to transmitting
        mgr.tx_enabled = True
        mgr.dispatch()
        self.assertTrue(isinstance(mgr.state, Manager.Transmitting))
        mgr.dispatch()
        self.assertFalse(mgr.is_faulted())

    def test_rx(self):
        mock = MockAx5043()
        mock.read_defaults[Reg.XTALSTATUS] = Bits.XTAL_RUN
        mock.read_defaults[Reg.POWSTAT] |= Bits.SVMODEM
        mgr = Manager(mock)
        # Transition to autoranging
        mgr.dispatch()
        # Transition to idle
        mgr.dispatch()
        # Transition to receiving
        mgr.rx_enabled = True
        mgr.dispatch()
        self.assertTrue(isinstance(mgr.state, Manager.Receiving))
        mgr.dispatch()
        self.assertFalse(mgr.is_faulted())

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
