import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "app")
)

from miner_controller import MinerController


class RuntimeHashTests(unittest.TestCase):

    def test_modified_engine_cannot_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "xmrig.exe"
            binary.write_bytes(b"altered test executable")

            with patch("miner_controller.subprocess.Popen") as launch:
                with self.assertRaisesRegex(
                    RuntimeError, "SHA-256 verification failed"
                ):
                    MinerController._launch_xmrig(
                        None, [str(binary)], binary, 0
                    )
                launch.assert_not_called()

    def test_missing_engine_cannot_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "xmrig.exe"

            with patch("miner_controller.subprocess.Popen") as launch:
                with self.assertRaises(RuntimeError):
                    MinerController._launch_xmrig(
                        None, [str(binary)], binary, 0
                    )
                launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
