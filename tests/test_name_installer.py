"""python -m unittest discover -s tests"""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import name_installer  # noqa: E402

OLD = "JengChat.Friends-friends-win-x64-Setup.exe"
NEW = "JengChat-setup.exe"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_release(folder, include_installer=True):
    """A releases folder shaped like build_release.py's output."""
    installer = b"setup bytes"
    files = {
        "release-metadata.json": json.dumps({"version": "3.0.0-beta.1", "installer": OLD,
                                             "installer_sha256": sha(installer)}).encode(),
        "assets.friends-win-x64.json": json.dumps([{"RelativeFileName": OLD, "Type": "Installer"},
                                                   {"RelativeFileName": "x-full.nupkg", "Type": "Full"}]).encode(),
        "x-full.nupkg": b"package",
    }
    if include_installer:
        files[OLD] = installer
    for name, body in files.items():
        (folder / name).write_bytes(body)
    digests = {**{n: sha(b) for n, b in files.items()}, OLD: sha(installer)}
    (folder / "SHA256SUMS.txt").write_text("".join(f"{digests[n]}  {n}\n" for n in sorted(digests)), encoding="utf-8")
    return installer


def sums(folder):
    lines = (folder / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    return {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in lines}


class NameInstallerTests(unittest.TestCase):
    def test_renames_the_installer_file(self):
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            installer = write_release(folder)
            name_installer.rename(folder, NEW)
            self.assertFalse((folder / OLD).exists())
            self.assertEqual((folder / NEW).read_bytes(), installer)

    def test_metadata_names_the_new_installer_with_the_same_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            installer = write_release(folder)
            name_installer.rename(folder, NEW)
            meta = json.loads((folder / "release-metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["installer"], NEW)
            self.assertEqual(meta["installer_sha256"], sha(installer))

    def test_checksums_list_the_new_name_and_match_every_file(self):
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            write_release(folder)
            name_installer.rename(folder, NEW)
            listed = sums(folder)
            self.assertNotIn(OLD, listed)
            for name, digest in listed.items():
                self.assertEqual(digest, sha((folder / name).read_bytes()), name)

    def test_velopack_asset_list_names_the_new_installer(self):
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            write_release(folder)
            name_installer.rename(folder, NEW)
            assets = json.loads((folder / "assets.friends-win-x64.json").read_text(encoding="utf-8"))
            self.assertEqual([a["RelativeFileName"] for a in assets], [NEW, "x-full.nupkg"])

    def test_works_on_the_small_files_alone_keeping_the_installer_checksum(self):
        # Used to fix an existing draft without downloading the 175 MB installer.
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            installer = write_release(folder, include_installer=False)
            name_installer.rename(folder, NEW)
            self.assertEqual(sums(folder)[NEW], sha(installer))

    def test_rejects_a_name_with_a_folder(self):
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            write_release(folder)
            with self.assertRaises(ValueError):
                name_installer.rename(folder, "../JengChat-setup.exe")


if __name__ == "__main__":
    unittest.main()
