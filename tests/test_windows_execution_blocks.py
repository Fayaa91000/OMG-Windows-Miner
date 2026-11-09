import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "app")
)

from miner_controller import MinerController

EXPECTED = (
    "6fa80698d7268f6e88aa88c06fb27ee99e1bcee747c"
    "2e76911e6206a5b1aeeb3"
)


class WindowsExecutionBlockTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.binary = Path(self.folder.name) / "xmrig.exe"
        self.binary.write_bytes(b"Harmless simulated executable")

    def simulate_launch(self, error):
        real_sha256 = hashlib.sha256

        class FakeDigest:
            def update(self, data):
                pass

            def hexdigest(self):
                return EXPECTED

        with patch.object(hashlib, "sha256",
                          side_effect=lambda: FakeDigest()):
            with patch(
                "miner_controller.subprocess.Popen",
                side_effect=error
            ) as launch:
                with self.assertRaises(type(error)):
                    MinerController._launch_xmrig(
                        None,
                        [str(self.binary)],
                        self.binary,
                        0
                    )
                launch.assert_called_once()

    def test_windows_access_denied(self):
        self.simulate_launch(
            PermissionError(13, "Access denied")
        )

    def test_windows_file_blocked_or_removed(self):
        self.simulate_launch(
            FileNotFoundError(2, "Executable unavailable")
        )

    def test_engine_hash_mismatch_prevents_launch(self):
        with patch(
            "miner_controller.subprocess.Popen"
        ) as launch:
            with self.assertRaisesRegex(
                RuntimeError, "SHA-256 verification failed"
            ):
                MinerController._launch_xmrig(
                    None,
                    [str(self.binary)],
                    self.binary,
                    0
                )
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
