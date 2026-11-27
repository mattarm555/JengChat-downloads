"""Before a draft is created: run the real publisher (publish_delivery.generate) on the built files.

Builds the release object GitHub would return for a published prerelease from a local releases folder
and lets publish_delivery verify it exactly as the publish workflow will (checksums, metadata, feed
entries, installer checksum, package id), writing the would-be Pages site to --output. A release that
would fail at publish time fails here instead, before anything public exists.

    python3 tools/check_draft.py --releases release --tag v3.0.0-beta.1 --output _check
    python3 tools/check_draft.py --party --releases release --tag party-v0.1.0-beta.1 --output _check
Development builds (--allow-development, local tests only) are checked with their own package id.
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import publish_delivery  # noqa: E402

OFFICIAL_FEED = "https://mattarm555.github.io/JengChat-downloads/updates/"


def local_release(folder, tag):
    base = f"https://github.com/{publish_delivery.REPO}/releases/download/{tag}/"
    files = {base + f.name: f for f in folder.iterdir() if f.is_file()}
    release = {"tag_name": tag, "draft": False, "prerelease": True,
               "html_url": f"https://github.com/{publish_delivery.REPO}/releases/tag/{tag}",
               "assets": [{"name": f.name, "browser_download_url": url} for url, f in files.items()]}
    return release, lambda url: files[url].read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--releases", type=pathlib.Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--template", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1] / "site")
    parser.add_argument("--allow-development", action="store_true")
    parser.add_argument("--party", action="store_true", help="a JengParty build (party-v tag, party/ feed)")
    args = parser.parse_args()
    release, fetch = local_release(args.releases.resolve(), args.tag)
    official = publish_delivery.PARTY_FEED if args.party else OFFICIAL_FEED
    index = f"releases.{publish_delivery.PARTY_CHANNEL if args.party else 'friends-win-x64'}.json"
    package = b'"JengParty"' if args.party else b'"JengChat.Friends"'
    if args.allow_development:
        # Local tests only: present a development build as the production publisher expects, to
        # exercise the same checks. Never used by the workflows.
        meta_name = "release-metadata.json"
        meta = json.loads((args.releases / meta_name).read_text(encoding="utf-8"))
        real = fetch

        def fetch(url, real=real):
            body = real(url)
            name = url.rsplit("/", 1)[1]
            if name == meta_name:
                body = json.dumps({**meta, "development": False, "feed": official}).encode()
            elif name == index:
                body = body.replace(package[:-1] + b'.Dev"', package)
            elif name == "SHA256SUMS.txt":
                import hashlib
                lines = []
                for line in body.decode().splitlines():
                    digest, file = line.split("  ", 1)
                    if file in (meta_name, index):
                        digest = hashlib.sha256(fetch(release_base(args.tag) + file)).hexdigest()
                    lines.append(digest + "  " + file)
                body = ("\n".join(lines) + "\n").encode()
            return body
    if args.party:
        publish_delivery.write_party(args.output, publish_delivery.verify_party(release, fetch, "passed"))
        info = json.loads((args.output / "party/release.json").read_text(encoding="utf-8"))
    else:
        publish_delivery.generate(release, fetch, args.template, args.output, "verified", "passed")
        info = json.loads((args.output / "release.json").read_text(encoding="utf-8"))
    print(f"Draft check passed for {info['version']}: the publisher accepts these assets")


def release_base(tag):
    return f"https://github.com/{publish_delivery.REPO}/releases/download/{tag}/"


if __name__ == "__main__":
    main()
