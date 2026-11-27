"""JengParty releases next to JengChat's on the same Pages site. python -m unittest discover -s tests"""
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import publish_delivery as pd  # noqa: E402

BASE = "https://github.com/mattarm555/JengChat-downloads/releases/download/"


def party_files(version="0.1.0-beta.1", **meta_changes):
    """The files the JengParty draft workflow uploads, as name -> bytes."""
    package = f"JengParty-{version}-party-win-x64-full.nupkg"
    files = {package: b"package " + version.encode(), "JengParty-setup.exe": b"installer " + version.encode()}
    feed = {"Assets": [{"PackageId": "JengParty", "Version": version, "Type": "Full", "FileName": package,
                        "SHA1": "", "SHA256": hashlib.sha256(files[package]).hexdigest(), "Size": len(files[package])}]}
    files["releases.party-win-x64.json"] = json.dumps(feed).encode()
    meta = {"version": version, "commit": "c0ffee", "game": "jengparty", "channel": "party-win-x64", "package_id": "JengParty",
            "feed": pd.PARTY_FEED, "installer": "JengParty-setup.exe",
            "installer_sha256": hashlib.sha256(files["JengParty-setup.exe"]).hexdigest(),
            "notes": "First build.\n", "development": False, **meta_changes}
    files["release-metadata.json"] = json.dumps(meta).encode()
    files["SHA256SUMS.txt"] = "".join(hashlib.sha256(b).hexdigest() + "  " + n + "\n" for n, b in sorted(files.items())).encode()
    return files


def release(tag, files, draft=False, prerelease=True, origin=BASE):
    urls = {origin + tag + "/" + name: body for name, body in files.items()}
    rel = {"tag_name": tag, "draft": draft, "prerelease": prerelease, "html_url": "https://github.com/x/releases/tag/" + tag,
           "assets": [{"name": url.rsplit("/", 1)[1], "browser_download_url": url} for url in urls]}
    return rel, lambda url: urls[url]


class PartyRelease(unittest.TestCase):
    def verify(self, tag="party-v0.1.0-beta.1", files=None, **kw):
        rel, fetch = release(tag, files or party_files(), **{k: v for k, v in kw.items() if k in ("draft", "prerelease", "origin")})
        return pd.verify_party(rel, fetch, kw.get("pilot_check", "passed"))

    def test_a_good_release_is_written_to_party(self):
        out = pathlib.Path(tempfile.mkdtemp())
        pd.write_party(out, self.verify())
        tag = "party-v0.1.0-beta.1"
        self.assertEqual((out / "party/source.txt").read_text(encoding="utf-8"), BASE + tag + "/\n")
        feed = json.loads((out / "party/releases.party-win-x64.json").read_text(encoding="utf-8"))
        self.assertEqual(feed["Assets"][0]["PackageId"], "JengParty")
        info = json.loads((out / "party/release.json").read_text(encoding="utf-8"))
        installer = party_files()["JengParty-setup.exe"]
        self.assertEqual(info["tag"], tag)
        self.assertEqual(info["version"], "0.1.0-beta.1")
        self.assertEqual(info["installer"], BASE + tag + "/JengParty-setup.exe")
        self.assertEqual(info["sha256"], hashlib.sha256(installer).hexdigest())
        self.assertEqual(info["size"], len(installer))
        self.assertEqual(info["acceptance"], {"second_machine_install_update": "passed"})

    def refused(self, **kw):
        with self.assertRaises(ValueError):
            self.verify(**kw)

    def test_development_builds_are_refused(self):
        self.refused(files=party_files(development=True))

    def test_another_feed_is_refused(self):
        self.refused(files=party_files(feed="https://mattarm555.github.io/JengChat-downloads/updates/"))

    def test_jengchat_metadata_is_refused(self):
        self.refused(files=party_files(game="godot"))

    def test_tags_must_be_party_tags_matching_the_version(self):
        self.refused(tag="v0.1.0-beta.1")
        self.refused(tag="party-v0.1.0-beta.2")

    def test_a_corrupt_asset_is_refused(self):
        files = party_files()
        files["JengParty-setup.exe"] = b"tampered"
        self.refused(files=files)

    def test_another_package_id_is_refused(self):
        files = party_files()
        files["releases.party-win-x64.json"] = files["releases.party-win-x64.json"].replace(b'"JengParty"', b'"JengParty.Dev"')
        files["SHA256SUMS.txt"] = "".join(hashlib.sha256(b).hexdigest() + "  " + n + "\n" for n, b in sorted(files.items()) if n != "SHA256SUMS.txt").encode()
        self.refused(files=files)

    def test_drafts_and_full_releases_are_refused(self):
        self.refused(draft=True)
        self.refused(prerelease=False)

    def test_assets_from_elsewhere_are_refused(self):
        self.refused(origin="https://github.com/someone/else/releases/download/")

    def test_no_pilot_waiver_exists_for_jengparty(self):
        self.refused(pilot_check="waived")


class LiveSite(unittest.TestCase):
    """Publishing one game keeps the other game's live release, verified again."""

    def get(self, pages):
        def get(url):
            if url not in pages:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO())
            return json.dumps(pages[url]).encode()
        return get

    def test_no_live_party_yet(self):
        self.assertIsNone(pd.live_party(self.get({})))

    def test_live_party_names_its_tag_and_acceptance(self):
        page = {"tag": "party-v0.1.0-beta.1", "acceptance": {"second_machine_install_update": "passed"}}
        self.assertEqual(pd.live_party(self.get({pd.SITE + "party/release.json": page})), ("party-v0.1.0-beta.1", "passed"))

    def test_live_jengchat_gives_its_tag_and_acceptance(self):
        page = {"version": "3.0.0-beta.2", "acceptance": {"second_machine_install_update": "waived", "second_machine_settings": "waived"}}
        self.assertEqual(pd.live_jengchat(self.get({pd.SITE + "release.json": page})), ("v3.0.0-beta.2", "waived", "waived"))

    def test_live_jengchat_must_exist(self):
        with self.assertRaises(ValueError):
            pd.live_jengchat(self.get({}))

    def test_other_errors_are_not_mistaken_for_no_party(self):
        def get(url):
            raise urllib.error.HTTPError(url, 503, "Unavailable", {}, io.BytesIO())
        with self.assertRaises(urllib.error.HTTPError):
            pd.live_party(get)


if __name__ == "__main__":
    unittest.main()
