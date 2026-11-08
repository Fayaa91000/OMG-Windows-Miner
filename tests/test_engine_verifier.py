import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.engine_verifier import verify_engine


class TestEngineVerifier(unittest.TestCase):

    def test_missing_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            ok, message = verify_engine(
                Path(folder) / "xmrig.exe"
            )
            self.assertFalse(ok)
            self.assertIn("missing", message.lower())

    def test_modified_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "xmrig.exe"
            path.write_bytes(b"modified executable")
            ok, message = verify_engine(path)
            self.assertFalse(ok)
            self.assertIn("mismatch", message.lower())

    def test_matching_fingerprint(self):
        payload = b"test-engine-content"
        expected = hashlib.sha256(payload).hexdigest()

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "xmrig.exe"
            path.write_bytes(payload)

            with patch(
                "app.engine_verifier.EXPECTED_SHA256",
                expected
            ):
                ok, message = verify_engine(path)

            self.assertTrue(ok)
            self.assertIn("verified", message.lower())


if __name__ == "__main__":
    unittest.main()
