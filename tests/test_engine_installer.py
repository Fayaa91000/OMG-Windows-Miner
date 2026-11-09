import hashlib
import io
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "app")
)

import engine_installer as installer


class FakeResponse(io.BytesIO):
    def geturl(self):
        return installer.URL


class EngineInstallerTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.exe_data = b"OMG test fixture - not mining software"

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(
                "xmrig-test/xmrig.exe",
                self.exe_data
            )

        self.zip_data = buffer.getvalue()
        self.zip_hash = hashlib.sha256(
            self.zip_data
        ).hexdigest()
        self.exe_hash = hashlib.sha256(
            self.exe_data
        ).hexdigest()

        self.target = (
            Path(self.temp.name)
            / "OMG Windows Miner"
            / "engine"
            / "xmrig.exe"
        )

    def run_install(self, scan_status="scan_completed",
                    zip_hash=None):

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(installer.sys, "platform", "win32")
            )
            stack.enter_context(
                patch.dict(
                    os.environ,
                    {"LOCALAPPDATA": self.temp.name}
                )
            )
            stack.enter_context(
                patch.object(
                    installer, "ZIP_HASH",
                    zip_hash if zip_hash is not None
                    else self.zip_hash
                )
            )
            stack.enter_context(
                patch.object(
                    installer, "EXE_HASH", self.exe_hash
                )
            )
            stack.enter_context(
                patch.object(
                    installer.urllib.request,
                    "urlopen",
                    return_value=FakeResponse(self.zip_data)
                )
            )
            scanner = stack.enter_context(
                patch.object(
                    installer,
                    "scan_engine",
                    return_value=(scan_status, "Test scan result")
                )
            )

            result = installer.install_engine(consent=True)
            return result, scanner.call_count

    def test_consent_required(self):
        status, _ = installer.install_engine(False)
        self.assertEqual(status, "consent_required")

    def test_non_windows_unavailable(self):
        with patch.object(installer.sys, "platform", "linux"):
            status, _ = installer.install_engine(True)
        self.assertEqual(status, "unavailable")

    def test_wrong_archive_hash_rejected(self):
        (status, _), scans = self.run_install(
            zip_hash="0" * 64
        )
        self.assertEqual(status, "unknown")
        self.assertEqual(scans, 0)
        self.assertFalse(self.target.exists())

    def test_defender_detection_prevents_install(self):
        (status, _), scans = self.run_install("detected")
        self.assertEqual(status, "detected")
        self.assertEqual(scans, 1)
        self.assertFalse(self.target.exists())

    def test_verified_install_requires_runtime_checks(self):
        (status, _), scans = self.run_install()
        self.assertEqual(
            status, "installed_pending_runtime_checks"
        )
        self.assertEqual(scans, 1)
        self.assertEqual(
            self.target.read_bytes(), self.exe_data
        )


if __name__ == "__main__":
    unittest.main()
