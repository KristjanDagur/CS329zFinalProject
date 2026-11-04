"""Install the pinned official OpenCode binary locally, without global changes."""
import base64
import hashlib
import io
import json
import platform
import tarfile
import urllib.request
from pathlib import Path

VERSION = "1.19.5"


def install():
    system = {"Darwin": "darwin", "Linux": "linux"}.get(platform.system())
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "AMD64": "x64"}.get(platform.machine())
    if not system or not arch:
        raise SystemExit("Install OpenCode 1.19.5 manually on this platform and use --opencode PATH.")
    package = f"opencode-{system}-{arch}"
    with urllib.request.urlopen(f"https://registry.npmjs.org/{package}/{VERSION}", timeout=30) as response:
        metadata = json.load(response)
    with urllib.request.urlopen(metadata["dist"]["tarball"], timeout=120) as response:
        raw = response.read()
    expected = metadata["dist"]["integrity"]
    actual = "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode()
    if actual != expected:
        raise SystemExit("OpenCode archive integrity mismatch; nothing was installed.")
    target = Path(__file__).resolve().parent / ".runtime" / "opencode"
    target.parent.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = [m for m in archive.getmembers() if m.isfile() and m.name.endswith("/opencode")]
        if len(members) != 1:
            raise SystemExit("Unexpected OpenCode package layout.")
        target.write_bytes(archive.extractfile(members[0]).read())
    target.chmod(0o755)
    print(f"Installed official {package}@{VERSION}: {target}")
    print("Verified npm SHA-512 integrity. No global configuration was changed.")


if __name__ == "__main__":
    install()
