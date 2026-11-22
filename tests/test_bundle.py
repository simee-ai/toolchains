import os
import tarfile
import zipfile

from toolchain_bundle.bundle import archive


def test_archive_formats_preserve_layout(tmp_path):
    root = tmp_path / "kicad-cli-1.0-x"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "kicad-cli").write_text("cli")
    for fmt in ("tar.gz", "tar.xz"):
        tar = archive(root, tmp_path / "out", fmt)
        assert tar.name == f"kicad-cli-1.0-x.{fmt}"
        with tarfile.open(tar) as t:
            assert "kicad-cli-1.0-x/bin/kicad-cli" in t.getnames()
    zf = archive(root, tmp_path / "out", "zip")
    with zipfile.ZipFile(zf) as z:
        assert "kicad-cli-1.0-x/bin/kicad-cli" in z.namelist()
