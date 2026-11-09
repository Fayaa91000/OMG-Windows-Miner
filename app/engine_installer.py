"""User-consented official XMRig installation for Windows.

No mining, Windows security bypass, or automatic threat allowance.
"""

import hashlib
import os
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from windows_security import scan_engine

URL = (
    "https://github.com/xmrig/xmrig/releases/download/"
    "v6.26.0/xmrig-6.26.0-windows-x64.zip"
)

ZIP_HASH = (
    "bba8097cb37d9b458a1cb1137876b27cde6740d17fe"
    "4ccbc086ba07d87d9e147"
)

EXE_HASH = (
    "6fa80698d7268f6e88aa88c06fb27ee99e1bcee747c"
    "2e76911e6206a5b1aeeb3"
)

MAX_ZIP = 60 * 1024 * 1024
MAX_EXE = 40 * 1024 * 1024


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def install_engine(consent=False):
    if not consent:
        return "consent_required", "XMRig agreement required."

    if sys.platform != "win32":
        return "unavailable", "Installation requires Windows."

    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return "unavailable", "Windows app directory unavailable."

    folder = Path(local) / "OMG Windows Miner" / "engine"
    target = folder / "xmrig.exe"

    try:
        if target.exists() or target.is_symlink():
            if target.is_file() and file_hash(target) == EXE_HASH:
                return (
                    "already_installed",
                    "Original XMRig verified. Runtime checks pending."
                )
            return "unknown", "Existing engine differs; not replaced."

        folder.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            prefix="omg-check-", dir=folder
        ) as work:
            archive = Path(work) / "xmrig.zip"
            staged = Path(work) / "xmrig.exe"

            with urllib.request.urlopen(URL, timeout=30) as response:
                if not response.geturl().startswith("https://"):
                    return "unknown", "Insecure download redirect."

                total = 0
                with archive.open("wb") as output:
                    while True:
                        block = response.read(1048576)
                        if not block:
                            break
                        total += len(block)
                        if total > MAX_ZIP:
                            return "unknown", "ZIP exceeds size limit."
                        output.write(block)

            if file_hash(archive) != ZIP_HASH:
                return "unknown", "XMRig ZIP checksum mismatch."

            with zipfile.ZipFile(archive) as package:
                matches = [
                    item for item in package.infolist()
                    if item.filename.replace("\\", "/")
                    .lower().endswith("/xmrig.exe")
                    and not item.is_dir()
                ]

                if len(matches) != 1:
                    return "unknown", "Unexpected XMRig archive."

                if matches[0].file_size > MAX_EXE:
                    return "unknown", "Engine exceeds size limit."

                size = 0
                with package.open(matches[0]) as source:
                    with staged.open("wb") as output:
                        while True:
                            block = source.read(1048576)
                            if not block:
                                break
                            size += len(block)
                            if size > MAX_EXE:
                                return "unknown", "Engine exceeds size limit."
                            output.write(block)

            if file_hash(staged) != EXE_HASH:
                return "unknown", "XMRig executable checksum mismatch."

            status, detail = scan_engine(staged)

            if status != "scan_completed":
                return status, detail

            if not staged.is_file():
                return "missing", "Windows removed the engine."

            if file_hash(staged) != EXE_HASH:
                return "unknown", "Engine changed during scan."

            if target.exists() or target.is_symlink():
                return "unknown", "Engine destination occupied."

            os.replace(staged, target)

            if file_hash(target) != EXE_HASH:
                return "unknown", "Installed file verification failed."

            return (
                "installed_pending_runtime_checks",
                "Verified XMRig installed. Windows execution "
                "permission and runtime checks remain pending."
            )

    except Exception as exc:
        return (
            "unknown",
            "Installation incomplete: " + type(exc).__name__
        )
