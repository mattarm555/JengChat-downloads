"""Give the built installer a plain download name, such as JengChat-setup.exe.

Velopack names it <package id>-<channel>-Setup.exe. Renaming it is safe: the installer carries its
package inside, and the update feed never refers to it. This renames the file (when present), points
release-metadata.json and Velopack's asset list at the new name, and rewrites SHA256SUMS.txt. The
installer's checksum is unchanged, so the small files can be fixed without the installer itself.

    python3 tools/name_installer.py --releases release --name JengChat-setup.exe
"""
import argparse
import hashlib
import json
import pathlib

META = "release-metadata.json"
SUMS = "SHA256SUMS.txt"


def rename(folder, new):
    folder = pathlib.Path(folder)
    if pathlib.PurePosixPath(new).name != new or pathlib.PureWindowsPath(new).name != new or not new.endswith(".exe"):
        raise ValueError("The installer name must be a plain .exe file name")
    meta = json.loads((folder / META).read_text(encoding="utf-8"))
    old = meta["installer"]
    if old == new:
        return
    if (folder / new).exists():
        raise ValueError(new + " already exists")
    if (folder / old).exists():
        (folder / old).rename(folder / new)
    meta["installer"] = new
    (folder / META).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    for manifest in folder.glob("assets.*.json"):
        assets = json.loads(manifest.read_text(encoding="utf-8"))
        for asset in assets:
            if asset.get("RelativeFileName") == old:
                asset["RelativeFileName"] = new
        manifest.write_text(json.dumps(assets) + "\n", encoding="utf-8")

    listed = {}
    for line in (folder / SUMS).read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed[new if name == old else name] = digest
    for name in listed:
        path = folder / name
        if path.exists():
            listed[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder / SUMS).write_text("".join(f"{listed[n]}  {n}\n" for n in sorted(listed)), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--releases", type=pathlib.Path, required=True)
    parser.add_argument("--name", default="JengChat-setup.exe")
    args = parser.parse_args()
    rename(args.releases, args.name)
    print("Installer named " + args.name)


if __name__ == "__main__":
    main()
