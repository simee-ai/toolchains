from toolchain_bundle.publish import next_tag, sha256sums


def test_next_tag_counts_builds_per_toolchain_version():
    assert next_tag("34.0", [], "wasi-sdk") == "wasi-sdk-34.0-1"
    assert next_tag("34.0", ["wasi-sdk-34.0-1", "wasi-sdk-33.0-3", "34.0"], "wasi-sdk") == "wasi-sdk-34.0-2"
    assert next_tag("34.0", ["wasi-sdk-34.0-1", "wasi-sdk-34.0-4"], "wasi-sdk") == "wasi-sdk-34.0-5"


def test_sha256sums_lists_every_asset(tmp_path):
    (tmp_path / "b.zip").write_bytes(b"b")
    (tmp_path / "a.tar.gz").write_bytes(b"a")
    lines = sha256sums(tmp_path).splitlines()
    assert [l.split("  ")[1] for l in lines] == ["a.tar.gz", "b.zip"]
    assert lines[0].split("  ")[0] == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
