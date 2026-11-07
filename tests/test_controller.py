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
            self.miner.LIMIT_SECONDS, 300
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


class TestGazaHandoff(unittest.TestCase):

    def test_user_process_stops_before_gaza_starts(self):
        from unittest.mock import patch
        from sadaqah_config import GAZA_WALLET

        class FakeProcess:
            def __init__(self):
                self.exited = False
                self.terminated = False

            def poll(self):
                return 0 if self.exited else None

            def terminate(self):
                self.terminated = True

            def wait(self, timeout=None):
                self.exited = True
                return 0

        miner = MinerController()
        old = FakeProcess()
        new = FakeProcess()

        miner.process = old
        miner.phase = "user"
        miner._mining_command = [
            "xmrig.exe",
            "-u", "4" + "A" * 94,
            "--threads=4",
            "--randomx-mode=light"
        ]

        miner.binary_path = lambda: Path(__file__)

        captured = []

        def fake_launch(command, binary, flags):
            self.assertTrue(old.exited)
            captured.extend(command)
            return new

        with patch.object(
            miner, "_launch_xmrig",
            side_effect=fake_launch
        ), patch("miner_controller.threading.Thread"):
            result = miner._switch_to_gaza()

        self.assertTrue(result)
        self.assertTrue(old.terminated)
        self.assertTrue(old.exited)
        self.assertIs(miner.process, new)
        self.assertEqual(miner.phase, "gaza")
        self.assertEqual(
            captured[captured.index("-u") + 1],
            GAZA_WALLET
        )
        self.assertIn("--threads=4", captured)
        self.assertIn("--randomx-mode=light", captured)


class TestHandoffCancellation(unittest.TestCase):

    def test_stop_during_handoff_prevents_gaza_launch(self):
        from unittest.mock import patch

        miner = MinerController()
        launched = []

        class FakeProcess:
            def poll(self):
                return None

            def terminate(self):
                pass

            def wait(self, timeout=None):
                # Simulate user pressing STOP during shutdown.
                miner._stop_requested.set()
                return 0

        miner.process = FakeProcess()
        miner.phase = "user"
        miner._mining_command = [
            "xmrig.exe",
            "-u", "4" + "A" * 94,
            "--threads=4"
        ]
        miner.binary_path = lambda: Path(__file__)

        def fake_launch(*args):
            launched.append(True)
            raise AssertionError(
                "Gaza miner must not launch after STOP"
            )

        with patch.object(
            miner, "_launch_xmrig",
            side_effect=fake_launch
        ):
            result = miner._switch_to_gaza()

        self.assertFalse(result)
        self.assertEqual(launched, [])
        self.assertIsNone(miner.process)
        self.assertEqual(miner.phase, "idle")
        self.assertFalse(miner._stopping)


class TestAutomaticSadaqahTimer(unittest.TestCase):

    def test_timer_triggers_gaza_handoff(self):
        import time
        from unittest.mock import patch

        miner = MinerController()
        fake = object()

        miner.process = fake
        miner.phase = "user"
        miner.started_at = (
            time.monotonic() - miner.USER_SECONDS - 2
        )

        with patch.object(
            miner, "_switch_to_gaza",
            return_value=True
        ) as switch:
            miner._watch_session(fake)

        switch.assert_called_once()

    def test_timer_completes_four_hour_session(self):
        import time
        from unittest.mock import patch

        miner = MinerController()
        fake = object()

        miner.process = fake
        miner.phase = "gaza"
        miner.started_at = (
            time.monotonic() - miner.LIMIT_SECONDS - 2
        )

        with patch.object(miner, "stop") as stop:
            miner._watch_session(fake)

        stop.assert_called_once_with(
            "Four-hour Sadaqah session completed"
        )


class TestLateHandoffCancellation(unittest.TestCase):

    def test_stop_requested_while_gaza_launches(self):
        from unittest.mock import patch

        miner = MinerController()

        class FakeProcess:
            def __init__(self):
                self.exited = False
                self.terminated = False

            def poll(self):
                return 0 if self.exited else None

            def terminate(self):
                self.terminated = True

            def wait(self, timeout=None):
                self.exited = True
                return 0

        old = FakeProcess()
        new = FakeProcess()

        miner.process = old
        miner.phase = "user"
        miner._mining_command = [
            "xmrig.exe",
            "-u", "4" + "A" * 94,
            "--threads=4"
        ]
        miner.binary_path = lambda: Path(__file__)

        def launch(*args):
            # STOP arrives after the initial cancellation
            # check, while the new process is launching.
            miner._stop_requested.set()
            return new

        with patch.object(
            miner, "_launch_xmrig",
            side_effect=launch
        ), patch("miner_controller.threading.Thread"):
            miner._switch_to_gaza()

        self.assertTrue(old.exited)
        self.assertTrue(new.terminated)
        self.assertTrue(new.exited)
        self.assertIsNone(miner.process)
        self.assertEqual(miner.phase, "idle")
        self.assertFalse(miner._stopping)
