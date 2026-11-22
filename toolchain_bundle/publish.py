"""Release tag numbering, checksums and publishing notes for the toolchains."""

import argparse
import hashlib
import re
from pathlib import Path
from typing import Callable


def next_tag(version: str, existing: list[str], prefix: str) -> str:
    """<prefix>-<version>-<n>: n counts our builds of that version."""
    pattern = rf"{re.escape(prefix)}-{re.escape(version)}-(\d+)"
    builds = [int(m.group(1)) for t in existing if (m := re.fullmatch(pattern, t))]
    return f"{prefix}-{version}-{max(builds, default=0) + 1}"


def sha256sums(dist: Path) -> str:
    lines = []
    for path in sorted(p for p in dist.iterdir() if p.is_file() and p.name != "SHA256SUMS"):
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    return "\n".join(lines) + "\n"



def toolchain_main(argv, version: str, prefix: str, notes: Callable[[str, str], str]) -> int:
    """The avr-gcc and arm-gcc workflows' release step: writes <dist>/SHA256SUMS and the notes
    (notes(run_url, sums)) and prints the release tag, <prefix>-<version>-<n>."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--tags", type=Path, required=True, help="file with existing release tags, one per line")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--notes", type=Path, default=Path("notes.md"))
    args = parser.parse_args(argv)

    sums = sha256sums(args.dist)
    (args.dist / "SHA256SUMS").write_text(sums)
    args.notes.write_text(notes(args.run_url, sums))
    print(next_tag(version, args.tags.read_text().split(), prefix))
    return 0
