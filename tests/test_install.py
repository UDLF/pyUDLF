"""
Installation of the UDLF binary (pyUDLF.install and the `pyudlf` command).

No network access: releases are served from local files (file:// URLs).
Set PYUDLF_RELEASE_ARCHIVE to the official Linux archive of UDLF v1.70
(udlf_v1-70_linux_x86-64.tar.gz) to also test the real release.
"""

import hashlib
import io
import os
import stat
import tarfile
from pathlib import Path

import numpy as np
import pytest

from pyUDLF import UDLF, UDLFError, UDLFNotFoundError, install
from pyUDLF.__main__ import main


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_archive(tmp_path, members=None):
    """A tar.gz shaped like the official release: ./bin/udlf, ./bin/config.ini,
    plus the macOS metadata files the official archive contains."""
    members = members or {
        f"./bin/{install.binary_name()}": b"#!/bin/sh\necho fake udlf\n",
        "./bin/config.ini": b"PARAM_NONE_L = 1000\n",
        "./bin/._udlf": b"apple double",
        "./._bin": b"apple double",
        "./.DS_Store": b"finder",
        "./LICENSE": b"GPL",
    }
    archive = tmp_path / "release.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o755 if name.endswith(("/udlf", "/udlf.exe")) else 0o644
            tar.addfile(info, io.BytesIO(content))
    return archive


@pytest.fixture
def fake_release(tmp_path, monkeypatch):
    """Replace the official releases by a local archive (version "9.9")."""
    archive = make_archive(tmp_path)
    releases = {"9.9": {install.platform_key(): (archive.as_uri(), _sha256(archive))}}
    monkeypatch.setattr(install, "RELEASES", releases)
    monkeypatch.setattr(install, "DEFAULT_VERSION", "9.9")
    return archive


# --------------------------------------------------------------------------
# download_udlf
# --------------------------------------------------------------------------

def test_download_installs_binary_and_config(fake_release, tmp_path):
    path = install.download_udlf("9.9", dest=tmp_path / "home")

    binary = tmp_path / "home" / "bin" / install.binary_name()
    assert path == str(binary)
    assert binary.read_bytes().startswith(b"#!/bin/sh")
    assert binary.stat().st_mode & stat.S_IXUSR
    assert (binary.parent / "config.ini").is_file()
    installed = sorted(p.name for p in (tmp_path / "home").rglob("*"))
    assert installed == ["bin", "config.ini", install.binary_name()]  # no ._*, .DS_Store


def test_windows_release_layout(tmp_path, monkeypatch):
    """Members of the official Windows archive of UDLF v1.70 (a .tar.gz, not a
    zip), as listed from the real file."""
    names = ["._.", "./._.DS_Store", "./.DS_Store", "./._LICENSE", "./LICENSE", "./._bin",
             "./._README.md", "./README.md", "./bin/._config.ini", "./bin/config.ini",
             "./bin/._udlf.exe", "./bin/udlf.exe"]
    archive = make_archive(tmp_path, {name: b"MZ" if name.endswith("udlf.exe") else b"x"
                                      for name in names})
    monkeypatch.setattr(install, "binary_name", lambda: "udlf.exe")
    monkeypatch.setattr(install, "platform_key", lambda: "windows-x86_64")
    monkeypatch.setattr(install, "RELEASES", {"9.9": {"windows-x86_64": (
        archive.as_uri(), _sha256(archive))}})

    path = install.download_udlf("9.9", dest=tmp_path / "home")

    assert path == str(tmp_path / "home" / "bin" / "udlf.exe")
    assert sorted(p.name for p in (tmp_path / "home" / "bin").iterdir()) == \
        ["config.ini", "udlf.exe"]


def test_installed_binary_is_not_downloaded_again(fake_release, tmp_path, monkeypatch):
    install.download_udlf("9.9", dest=tmp_path / "home")
    monkeypatch.setattr(install, "_fetch", lambda *a: pytest.fail("downloaded again"))

    assert install.download_udlf("9.9", dest=tmp_path / "home")


def test_force_downloads_again(fake_release, tmp_path):
    binary = Path(install.download_udlf("9.9", dest=tmp_path / "home"))
    binary.write_bytes(b"old")

    install.download_udlf("9.9", dest=tmp_path / "home", force=True)
    assert binary.read_bytes().startswith(b"#!/bin/sh")


def test_wrong_checksum_installs_nothing(fake_release, tmp_path, monkeypatch):
    key = install.platform_key()
    monkeypatch.setitem(install.RELEASES["9.9"], key, (fake_release.as_uri(), "0" * 64))

    with pytest.raises(UDLFError, match="SHA-256"):
        install.download_udlf("9.9", dest=tmp_path / "home")
    assert not (tmp_path / "home").exists()


def test_unsafe_archive_is_rejected(tmp_path, monkeypatch):
    archive = make_archive(tmp_path, {"./bin/udlf": b"x", "../evil.txt": b"x"})
    monkeypatch.setattr(install, "RELEASES",
                        {"9.9": {install.platform_key(): (archive.as_uri(), _sha256(archive))}})

    with pytest.raises(UDLFError, match="Unsafe path"):
        install.download_udlf("9.9", dest=tmp_path / "home")
    assert not (tmp_path / "evil.txt").exists()


def test_download_failure(tmp_path, monkeypatch):
    missing = (tmp_path / "missing.tar.gz").as_uri()
    monkeypatch.setattr(install, "RELEASES", {"9.9": {install.platform_key(): (missing, "")}})

    with pytest.raises(UDLFError, match="Could not download"):
        install.download_udlf("9.9", dest=tmp_path / "home")


def test_unknown_version_and_platform(tmp_path, monkeypatch):
    with pytest.raises(UDLFNotFoundError, match="Unknown UDLF version"):
        install.download_udlf("0.1", dest=tmp_path)
    monkeypatch.setattr(install, "platform_key", lambda: None)
    with pytest.raises(UDLFNotFoundError, match="Build UDLF from source"):
        install.download_udlf(install.DEFAULT_VERSION, dest=tmp_path)


def test_official_releases_are_pinned():
    for version, builds in install.RELEASES.items():
        for key, (url, sha256) in builds.items():
            assert url.startswith(f"https://github.com/UDLF/UDLF/releases/download/v{version}/")
            assert len(sha256) == 64


def test_pyudlf_home(monkeypatch, tmp_path):
    monkeypatch.setenv("PYUDLF_HOME", str(tmp_path))
    assert install.default_binary_path() == tmp_path / "bin" / install.binary_name()


def test_udlf_uses_the_installed_binary(fake_release, tmp_path, monkeypatch):
    monkeypatch.delenv("UDLF_BIN", raising=False)
    monkeypatch.setenv("PYUDLF_HOME", str(tmp_path / "home"))
    with pytest.raises(UDLFNotFoundError, match="pyudlf download"):
        UDLF()

    install.download_udlf("9.9")
    assert UDLF().bin_path == str(install.default_binary_path())


# --------------------------------------------------------------------------
# Legacy API: automatic installation when the default binary is missing
# --------------------------------------------------------------------------

def test_legacy_verify_bin_installs_missing_default_binary(fake_release, tmp_path,
                                                           monkeypatch):
    from pyUDLF import run_calls

    home = tmp_path / "home"
    default = str(home / "bin" / install.binary_name())
    monkeypatch.setattr(run_calls, "pyudlf_dir", home)
    monkeypatch.setattr(run_calls, "original_bin_path", default)

    run_calls.verify_bin(run_calls.config_path, default)
    assert Path(default).is_file()


def test_legacy_verify_bin_does_not_download_for_custom_path(fake_release, tmp_path,
                                                             monkeypatch, caplog):
    from pyUDLF import run_calls

    monkeypatch.setattr(install, "_fetch", lambda *a: pytest.fail("must not download"))
    run_calls.verify_bin(run_calls.config_path, str(tmp_path / "custom" / "udlf"))
    assert "not found" in caplog.text


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def test_cli_download(fake_release, tmp_path, capsys):
    dest = str(tmp_path / "home")
    assert main(["download", "--version", "9.9", "--dest", dest]) == 0
    assert "UDLF installed at" in capsys.readouterr().out
    assert main(["download", "--version", "9.9", "--dest", dest]) == 0
    assert "already installed" in capsys.readouterr().out
    assert main(["download", "--version", "9.9", "--dest", dest, "--force"]) == 0
    assert "UDLF installed at" in capsys.readouterr().out


def test_cli_where(udlf_bin, monkeypatch, capsys):
    monkeypatch.setenv("UDLF_BIN", str(udlf_bin))
    assert main(["where"]) == 0
    assert capsys.readouterr().out.strip() == str(udlf_bin)


def test_cli_where_without_binary(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("UDLF_BIN", raising=False)
    monkeypatch.setenv("PYUDLF_HOME", str(tmp_path))
    assert main(["where"]) == 1
    assert "pyudlf download" in capsys.readouterr().err


def test_cli_methods_and_describe(capsys):
    assert main(["methods"]) == 0
    assert "CPRR" in capsys.readouterr().out.split()
    assert main(["describe", "cprr"]) == 0
    assert "k = 20" in capsys.readouterr().out


# --------------------------------------------------------------------------
# Official release (optional, needs the archive file)
# --------------------------------------------------------------------------

@pytest.mark.skipif(not os.environ.get("PYUDLF_RELEASE_ARCHIVE"),
                    reason="set PYUDLF_RELEASE_ARCHIVE to the official UDLF v1.70 archive")
def test_official_release_installs_a_working_udlf(tmp_path, monkeypatch, udlf_bin, data):
    archive = Path(os.environ["PYUDLF_RELEASE_ARCHIVE"])
    url, sha256 = install.RELEASES["1.70"]["linux-x86_64"]
    assert _sha256(archive) == sha256  # it is the official file
    monkeypatch.setitem(install.RELEASES["1.70"], "linux-x86_64", (archive.as_uri(), sha256))

    binary = install.download_udlf("1.70", dest=tmp_path / "home")

    rks = np.loadtxt(data["rk_num"], dtype=int)
    official = UDLF(bin_path=binary).run("CPRR", ranked_lists=rks, params={"l": 100})
    built = UDLF(bin_path=udlf_bin).run("CPRR", ranked_lists=rks, params={"l": 100})
    np.testing.assert_array_equal(official.ranked_lists, built.ranked_lists)
