import hashlib
import json
import os
import time

import pytest

from arm_toolchain import components as arm_components
from avr_toolchain import components as avr_components
from toolchain_bundle import cache, debian
from wasm_toolchain import components as wasm_components

DAY = 24 * 3600


def _file(path, age_days=0.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    t = time.time() - age_days * DAY
    os.utime(path, (t, t))
    return path


def test_reusing_a_cached_debian_source_marks_it_used(tmp_path, monkeypatch):
    monkeypatch.setattr(debian, "SOURCE_FILES", {})
    orig = b"orig"
    dsc = ("Source: cairo\nVersion: 1.18.4-1\nChecksums-Sha1:\n"
           f" {hashlib.sha1(orig).hexdigest()} {len(orig)} cairo_1.18.4.orig.tar.xz\n").encode()
    files = {hashlib.sha1(data).hexdigest(): (name, data)
             for name, data in {"cairo_1.18.4-1.dsc": dsc, "cairo_1.18.4.orig.tar.xz": orig}.items()}

    def fetch(url):
        if url.endswith("srcfiles?fileinfo=0"):
            return json.dumps({"result": [{"hash": sha1} for sha1 in files]}).encode()
        sha1 = url.rsplit("/", 2)[1]
        if url == f"https://snapshot.debian.org/mr/file/{sha1}/info":
            return json.dumps({"hash": sha1, "result": [{"name": files[sha1][0]}]}).encode()
        raise AssertionError(f"a cached source should not need another download: {url}")

    sources = tmp_path / cache.DEBIAN_SOURCES
    olds = []
    for sha1, (name, data) in files.items():
        old = _file(sources / sha1[:2] / sha1 / name, age_days=cache.SOURCES_MAX_AGE_DAYS + 1)
        old.write_bytes(data)
        os.utime(old, (0, 0))
        olds.append(old)
    debian.sources_archive({("cairo", "1.18.4-1")}, tmp_path / "s.tar", sources, fetch=fetch)
    cache.prune(tmp_path)
    assert all(old.exists() for old in olds)


TOOLCHAIN_SOURCES = pytest.mark.parametrize("components", [wasm_components, arm_components, avr_components],
                                            ids=["wasi-sdk", "arm-gcc", "avr-gcc"])


@TOOLCHAIN_SOURCES
def test_prune_drops_toolchain_archives_no_recent_build_used(tmp_path, components):
    sources = tmp_path / components.SOURCES_CACHE
    fresh = _file(sources / "ab" / "ab12" / "fresh.tar.xz", age_days=cache.SOURCES_MAX_AGE_DAYS - 1)
    stale = _file(sources / "cd" / "cd34" / "stale.tar.xz", age_days=cache.SOURCES_MAX_AGE_DAYS + 1)
    cache.prune(tmp_path)
    assert fresh.exists() and not stale.exists() and not stale.parent.parent.exists()


@TOOLCHAIN_SOURCES
def test_reusing_a_cached_toolchain_archive_marks_it_used(tmp_path, monkeypatch, components):
    data = b"archive"
    digest = hashlib.sha256(data).hexdigest()

    def offline(url):
        raise AssertionError(f"a cached archive should not need another download: {url}")

    if components is avr_components:
        source = avr_components.Source("gmp", "6.3.0", "https://example.invalid/gmp-6.3.0.tar.xz", digest, "LGPL")
        monkeypatch.setattr(avr_components, "SOURCES", (source,))
        name, refetch = source.archive, lambda: avr_components.fetch(tmp_path, get=offline)
    else:
        download = components.Download("thing.tar.xz", "https://example.invalid/thing.tar.xz", digest)
        name, refetch = download.archive, lambda: components.fetch(download, tmp_path, get=offline)
    old = _file(tmp_path / components.SOURCES_CACHE / digest[:2] / digest / name)
    old.write_bytes(data)
    os.utime(old, (0, 0))
    refetch()
    cache.prune(tmp_path)
    assert old.exists() and old.stat().st_mtime > time.time() - DAY
