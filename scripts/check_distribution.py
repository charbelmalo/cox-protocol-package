#!/usr/bin/env python3
"""Check built artifacts themselves, including resource coverage and exclusions."""

from __future__ import annotations
import argparse
import json
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(dist: Path, vsix: Path):
    version = json.loads((ROOT / "package.json").read_text())["version"]
    with zipfile.ZipFile(
        dist / f"cox_protocol_package-{version}-py3-none-any.whl"
    ) as archive:
        wheel = archive.namelist()
        assert "cox_protocol/__main__.py" in wheel
        assert (
            len([name for name in wheel if name.startswith("cox_protocol/schemas/")])
            == 5
        )
        assert "cox_protocol/starter/page/action_button/reference.svg" in wheel
        assert not any(name.startswith("tools/") for name in wheel)
        for name in wheel:
            if name.startswith("cox_protocol/"):
                assert archive.read(name) == (ROOT / name).read_bytes(), name
    with tarfile.open(dist / f"cox_protocol_package-{version}.tar.gz") as archive:
        source = archive.getnames()
        assert any(name.endswith("/tests/test_compiler.py") for name in source)
        assert any(name.endswith("/scripts/release_check.py") for name in source)
    with tarfile.open(dist / f"cox-protocol-package-{version}.tgz") as archive:
        npm = archive.getnames()
        assert "package/cox_protocol/starter/manifest.cox" in npm
        assert "package/bin/cox-protocol.js" in npm
        assert (
            json.load(archive.extractfile("package/package.json"))["version"] == version
        )
    with zipfile.ZipFile(vsix) as archive:
        extension = archive.namelist()
        package = json.loads(archive.read("extension/package.json"))
        assert package["version"] == version
        assert package["contributes"]["languages"][0]["id"] == "cox"
        for item in package["contributes"]["snippets"]:
            assert "extension/" + item["path"].removeprefix("./") in extension
    for label, names in [
        ("wheel", wheel),
        ("sdist", source),
        ("npm", npm),
        ("VSIX", extension),
    ]:
        for name in names:
            parts = Path(name).parts
            assert not set(parts) & {
                "node_modules",
                "__pycache__",
                ".git",
                ".venv",
                "build",
            }, (label, name)
            assert not name.endswith((".pyc", ".pyo", ".cox-build.json")), (label, name)
    print(
        json.dumps(
            {
                "ok": True,
                "version": version,
                "artifacts": ["wheel", "sdist", "npm", "VSIX"],
                "checks": [
                    "resources",
                    "source-byte-match",
                    "versions",
                    "snippets",
                    "no-transient-files",
                ],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--vsix", type=Path, required=True)
    args = parser.parse_args()
    check(args.dist, args.vsix)
