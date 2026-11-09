import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess, TimeoutExpired

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import windows_security


class WindowsSecurityTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.engine = Path(self.folder.name) / "xmrig.exe"
        self.engine.write_bytes(b"test only, not a miner")

    def tearDown(self):
        self.folder.cleanup()

    def check(self, result):
        with patch.object(windows_security.sys, "platform", "win32"):
            with patch.object(
                windows_security.subprocess,
                "run",
                return_value=result
            ):
                return windows_security.scan_engine(self.engine)

    def test_detection_blocks(self):
        result = CompletedProcess(
            [], 0, stdout="OMG_SCAN_RESULT:DETECTION"
        )
        self.assertEqual(self.check(result)[0], "detected")

    def test_scan_failure_blocks(self):
        result = CompletedProcess(
            [], 1, stdout="OMG_SCAN_RESULT:UNKNOWN"
        )
        self.assertEqual(self.check(result)[0], "unknown")

    def test_no_matching_detection_is_not_approval(self):
        result = CompletedProcess(
            [], 0,
            stdout="OMG_SCAN_RESULT:NO_MATCHING_DETECTION"
        )
        status, message = self.check(result)
        self.assertEqual(status, "scan_completed")
        self.assertIn("not proof of safety", message)

    def test_unexpected_result_blocks(self):
        result = CompletedProcess([], 0, stdout="")
        self.assertEqual(self.check(result)[0], "unknown")

    def test_timeout_blocks(self):
        with patch.object(windows_security.sys, "platform", "win32"):
            with patch.object(
                windows_security.subprocess,
                "run",
                side_effect=TimeoutExpired("powershell.exe", 300)
            ):
                status, _ = windows_security.scan_engine(self.engine)
        self.assertEqual(status, "unknown")


if __name__ == "__main__":
    unittest.main()
