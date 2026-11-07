import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "app")
)

from miner_controller import MinerController


class TestMinerController(unittest.TestCase):

    def setUp(self):
        self.miner = MinerController()
        self.wallet = "4" + "A" * 94

    def test_empty_wallet_rejected(self):
        with self.assertRaises(ValueError):
            self.miner.start("")

    def test_invalid_wallet_rejected(self):
        with self.assertRaises(ValueError):
            self.miner.start("not-a-monero-wallet")

    def test_zero_threads_rejected(self):
        with self.assertRaises(ValueError):
            self.miner.start(self.wallet, threads=0)

    def test_above_six_threads_rejected(self):
        with self.assertRaises(ValueError):
            self.miner.start(self.wallet, threads=7)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            self.miner.start(self.wallet, mode="turbo")

    def test_session_limit(self):
        self.assertEqual(
            self.miner.LIMIT_SECONDS, 14400
        )


if __name__ == "__main__":
    unittest.main()


class TestMinerStop(unittest.TestCase):

    def test_stop_terminates_process(self):
        import time

        class FakeProcess:
            def __init__(self):
                self.terminated = False

            def poll(self):
                return None

            def terminate(self):
                self.terminated = True

            def wait(self, timeout=None):
                return 0

        miner = MinerController()
        fake = FakeProcess()

        miner.process = fake
        miner.started_at = time.monotonic()

        miner.stop("Stopped by user")

        self.assertTrue(fake.terminated)
        self.assertIsNone(miner.process)

    def test_stop_when_idle(self):
        miner = MinerController()
        miner.stop()
        self.assertIsNone(miner.process)


class TestRapidRestart(unittest.TestCase):

    def test_start_blocked_while_stopping(self):
        import threading
        import time

        class SlowProcess:
            def __init__(self):
                self.terminated = threading.Event()
                self.allow_exit = threading.Event()

            def poll(self):
                return None

            def terminate(self):
                self.terminated.set()

            def wait(self, timeout=None):
                if not self.allow_exit.wait(timeout=2):
                    raise RuntimeError("Test shutdown timed out")
                return 0

        miner = MinerController()
        fake = SlowProcess()
        miner.process = fake
        miner.started_at = time.monotonic()

        worker = threading.Thread(target=miner.stop)
        worker.start()

        try:
            self.assertTrue(fake.terminated.wait(timeout=2))

            # Use an existing file to pass the binary-presence check.
            miner.binary_path = lambda: Path(__file__)

            with self.assertRaises(RuntimeError):
                miner.start("4" + "A" * 94, 3, "auto")

        finally:
            fake.allow_exit.set()
            worker.join(timeout=3)

        self.assertFalse(worker.is_alive())
        self.assertIsNone(miner.process)
        self.assertFalse(miner._stopping)
