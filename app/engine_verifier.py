"""Verify the independent XMRig executable before use."""

from pathlib import Path
import hashlib

XMRIG_VERSION = "6.26.0"

EXPECTED_SHA256 = (
    "6fa80698d7268f6e88aa88c06fb27"
    "ee99e1bcee747c2e76911e6206a5b1aeeb3"
)


def verify_engine(path):
    path = Path(path)

    if not path.is_file():
        return False, "XMRig executable is missing."

    digest = hashlib.sha256()

    try:
        with path.open("rb") as executable:
            for chunk in iter(
                lambda: executable.read(1024 * 1024),
                b""
            ):
                digest.update(chunk)
    except OSError:
        return False, "Unable to read XMRig executable."

    if digest.hexdigest() != EXPECTED_SHA256:
        return False, "XMRig SHA-256 mismatch."

    return True, "XMRig 6.26.0 SHA-256 verified."
