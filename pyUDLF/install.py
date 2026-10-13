"""
Installation of the UDLF binary.

pyUDLF never downloads anything implicitly through the high-level API
(pyUDLF.UDLF). The binary is installed explicitly with

    python -m pyUDLF download          # or: pyudlf download

or pyUDLF.install.download_udlf(). Official releases are downloaded over
https from GitHub and checked against their SHA-256 before installation.
On platforms without an official build (e.g. macOS), build UDLF from source
(scripts/build_udlf.sh in the pyUDLF repository) and pass its path.

The installation directory is ~/.pyudlf, or the PYUDLF_HOME environment
variable.
"""

import hashlib
import os
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

from pyUDLF.errors import UDLFError, UDLFNotFoundError

DEFAULT_VERSION = "1.70"

# Official UDLF releases: {version: {platform: (url, sha256)}}
# Digests published by GitHub for the release assets.
RELEASES = {
    "1.70": {
        "linux-x86_64": (
            "https://github.com/UDLF/UDLF/releases/download/v1.70/"
            "udlf_v1-70_linux_x86-64.tar.gz",
            "eaea5df9290cfb0ac9bf22eaf08765994914df994390c5f95d3387449e8a0530"),
        "windows-x86_64": (
            "https://github.com/UDLF/UDLF/releases/download/v1.70/"
            "udlf_v1-70_windows_x86-64.tar.gz",
            "42c5844b01c26f82dcf88d76f3640845d18a513ebd7967a34b83acb5694d2d36"),
    },
}

BUILD_HINT = ("Build UDLF from source (https://github.com/UDLF/UDLF: run `make`, or "
              "scripts/build_udlf.sh in the pyUDLF repository) and pass its path with "
              "bin_path= or the UDLF_BIN environment variable.")


def pyudlf_home() -> Path:
    """Directory where pyUDLF installs UDLF (PYUDLF_HOME or ~/.pyudlf)."""
    return Path(os.path.expanduser(os.environ.get("PYUDLF_HOME", "~/.pyudlf")))


def binary_name() -> str:
    return "udlf.exe" if sys.platform.startswith("win") else "udlf"


def default_binary_path() -> Path:
    """Where download_udlf() installs the binary."""
    return pyudlf_home() / "bin" / binary_name()


def platform_key():
    """Key of the current platform in RELEASES, or None if not supported."""
    machine = platform.machine().lower()
    arch = "x86_64" if machine in ("x86_64", "amd64") else machine
    if sys.platform.startswith("linux"):
        return f"linux-{arch}"
    if sys.platform.startswith("win"):
        return f"windows-{arch}"
    return None


def download_udlf(version: str = None, dest=None, force: bool = False) -> str:
    """
    Download an official UDLF release and install its binary.

    Args:
        version (str, optional): UDLF version (see RELEASES); default DEFAULT_VERSION.
        dest (str, optional): installation directory; default pyudlf_home().
            The binary is installed at <dest>/bin/udlf (udlf.exe on Windows),
            next to the release config.ini.
        force (bool): download again even if the binary is already installed.

    Returns:
        str: path of the installed binary.

    Raises:
        UDLFNotFoundError: no official build for this platform or version.
        UDLFError: download failed or the archive is not the expected one.
    """
    version = version or DEFAULT_VERSION
    dest = Path(os.path.expanduser(str(dest))) if dest is not None else pyudlf_home()
    target = dest / "bin" / binary_name()
    if target.is_file() and not force:
        return str(target)

    if version not in RELEASES:
        raise UDLFNotFoundError(f"Unknown UDLF version {version!r}. "
                                f"Available: {sorted(RELEASES)}. {BUILD_HINT}")
    key = platform_key()
    if key not in RELEASES[version]:
        raise UDLFNotFoundError(f"There is no official UDLF {version} build for this "
                                f"platform ({sys.platform}, {platform.machine()}). "
                                + BUILD_HINT)
    url, sha256 = RELEASES[version][key]

    with tempfile.TemporaryDirectory(prefix="pyudlf_download_") as tmp:
        archive = Path(tmp) / "udlf.tar.gz"
        _fetch(url, archive)
        digest = _sha256(archive)
        if digest != sha256:
            raise UDLFError(f"The file downloaded from {url} is not the official UDLF "
                            f"{version} release (SHA-256 {digest}, expected {sha256}). "
                            "Nothing was installed.")
        extracted = Path(tmp) / "extracted"
        _safe_extract(archive, extracted)
        binary = _find_file(extracted, binary_name())
        config = binary.parent / "config.ini"

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(binary, target)
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        if config.is_file():
            shutil.copyfile(config, target.parent / "config.ini")

    return str(target)


def _fetch(url, path, timeout=60):
    """Download url to path."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response, \
                open(path, "wb") as f:
            shutil.copyfileobj(response, f)
    except OSError as e:  # URLError and HTTPError are OSErrors
        raise UDLFError(f"Could not download {url}: {e}") from e


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(archive, dest):
    """Extract regular files and directories of a tar archive into dest.

    Members with absolute paths or '..' are rejected; links, devices and
    macOS metadata files ('._*', '.DS_Store') are skipped."""
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:*") as tar:
        for member in tar.getmembers():
            parts = PurePosixPath(member.name).parts
            if member.name.startswith("/") or ".." in parts:
                raise UDLFError(f"Unsafe path in the UDLF archive: {member.name!r}")
            name = parts[-1] if parts else ""
            if name.startswith("._") or name == ".DS_Store":
                continue
            if member.isdir():
                (dest / member.name).mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                out = dest / member.name
                out.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, open(out, "wb") as dst:
                    shutil.copyfileobj(src, dst)


def _find_file(root, name):
    """The file called `name` in root (preferring a bin/ directory)."""
    found = sorted((p for p in root.rglob(name) if p.is_file()),
                   key=lambda p: (p.parent.name != "bin", len(p.parts)))
    if not found:
        raise UDLFError(f"The UDLF archive has no {name!r} file.")
    return found[0]
