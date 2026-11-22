"""Archive toolchain trees and remove previous builds."""

import shutil
import tarfile
import time
from pathlib import Path


def archive(root: Path, out_dir: Path, fmt: str) -> Path:
    """root/ as out_dir/<root name>.tar.gz, .tar.xz or .zip, with root's name as the top-level folder."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if fmt in ("tar.gz", "tar.xz"):
        dest = out_dir / f"{root.name}.{fmt}"
        with tarfile.open(dest, f"w:{fmt[4:]}") as tar:
            tar.add(root, arcname=root.name)  # keeps symlinks as symlinks
        return dest
    dest = Path(shutil.make_archive(str(out_dir / root.name), "zip", root.parent, root.name))
    return dest


def remove(path: Path, tries: int = 5) -> None:
    """rmtree that also removes read-only files and folders (Homebrew bottles ship some), retried
    because Finder may drop a .DS_Store into a folder while it's being deleted."""
    def writable(func, name, _):
        Path(name).parent.chmod(0o755)
        Path(name).chmod(0o755)
        func(name)

    for attempt in range(tries):
        try:
            shutil.rmtree(path, onerror=writable)
            return
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(1)
