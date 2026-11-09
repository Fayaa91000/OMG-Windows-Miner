import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from miner_controller import MinerController


class InitialMiningCommandTests(unittest.TestCase):

    def test_initial_command_is_transparent(self):
        miner = MinerController()
        wallet = "4" + "A" * 94
        captured = []

        class FakeProcess:
            pass

        miner.binary_path = lambda: Path(__file__)

        def fake_launch(command, binary, flags):
            captured.extend(command)
            return FakeProcess()

        with patch.object(
            miner, "_launch_xmrig", side_effect=fake_launch
        ), patch("miner_controller.threading.Thread"):
            miner.start(wallet, 3, "light")

        self.assertEqual(captured[captured.index("-u") + 1], wallet)
        self.assertEqual(
            captured[captured.index("-o") + 1],
            "pool.hashvault.pro:443"
        )
        self.assertIn("--tls", captured)
        self.assertIn("--coin", captured)
        self.assertIn("--algo", captured)
        self.assertIn("--threads=3", captured)
        self.assertIn("--randomx-mode=light", captured)
        self.assertIn("--pause-on-battery", captured)
        self.assertNotIn("--background", captured)


if __name__ == "__main__":
    unittest.main()
