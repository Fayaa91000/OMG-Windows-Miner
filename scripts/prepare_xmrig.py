from pathlib import Path
import hashlib
import urllib.request
import zipfile

VERSION = "6.26.0"
NAME = f"xmrig-{VERSION}-windows-x64.zip"
URL = (
    f"https://github.com/xmrig/xmrig/releases/"
    f"download/v{VERSION}/{NAME}"
)
EXPECTED = (
    "bba8097cb37d9b458a1cb1137876b27cde6740d17fe"
    "4ccbc086ba07d87d9e147"
)

vendor = Path("vendor")
vendor.mkdir(exist_ok=True)
archive = vendor / NAME
target = vendor / "xmrig.exe"

if not archive.exists():
    urllib.request.urlretrieve(URL, archive)

actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != EXPECTED:
    raise SystemExit("XMRig checksum mismatch. Build stopped.")

with zipfile.ZipFile(archive) as z:
    matches = [
        name for name in z.namelist()
        if name.lower().endswith("/xmrig.exe")
    ]
    if len(matches) != 1:
        raise SystemExit("XMRig executable missing or duplicated.")
    target.write_bytes(z.read(matches[0]))

print("Verified Windows XMRig prepared for packaging")
