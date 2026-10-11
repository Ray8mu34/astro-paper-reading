"""Verify the ZIP and, optionally, every installed file against its manifest."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip",type=Path)
    p.add_argument("--installed",type=Path)
    args=p.parse_args()
    with zipfile.ZipFile(args.zip) as z:
        if z.testzip():raise ValueError("Invalid ZIP CRC")
        manifest=json.loads(z.read("astro-paper-reading/RELEASE-MANIFEST.json"))
        for row in manifest:
            name=row["path"]
            if not name.startswith("astro-paper-reading/") or ".." in Path(name).parts:raise ValueError("Unsafe archive path")
            content=z.read(name)
            if len(content)!=row["bytes"] or hashlib.sha256(content).hexdigest()!=row["sha256"]:raise ValueError(f"ZIP hash mismatch: {name}")
            if args.installed:
                path=args.installed/Path(name).relative_to("astro-paper-reading")
                if hashlib.sha256(path.read_bytes()).hexdigest()!=row["sha256"]:raise ValueError(f"Installed hash mismatch: {path}")
        print(f"PASS: {len(manifest)} file hashes, ZIP CRC"+", actual installed bytes" if args.installed else f"PASS: {len(manifest)} file hashes, ZIP CRC")


if __name__=="__main__":main()
