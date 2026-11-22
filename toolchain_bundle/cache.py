"""Expire source archives that no toolchain build has used in three months."""

import shutil
import time
from pathlib import Path

# Keep existing cached downloads available after the move from simee-kicad.
DEFAULT = Path.home() / ".cache" / "kicad-bundle"
DEBIAN_SOURCES = "debian-sources"
AVR_GCC_SOURCES = "avr-gcc-sources"  # avr_toolchain's upstream source archives
ARM_GCC_SOURCES = "arm-gcc-sources"  # arm_toolchain's Arm snapshot
WASI_SDK = "wasi-sdk"  # wasm_toolchain's wasi-sdk release archives, one per host (over 1 GB together)
SOURCES_MAX_AGE_DAYS = 90
SOURCES = (DEBIAN_SOURCES, AVR_GCC_SOURCES, ARM_GCC_SOURCES, WASI_SDK)


def prune(cache: Path) -> None:
    cutoff = time.time() - SOURCES_MAX_AGE_DAYS * 24 * 3600
    for sources in SOURCES:
        _prune_unused(cache / sources, cutoff)


def _prune_unused(root: Path, cutoff: float) -> None:
    """Delete files under root last used (mtime) before cutoff, then the folders that leaves empty."""
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
    for folder in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()
