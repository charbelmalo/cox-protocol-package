"""Portable, deterministic archives with an independently checkable file inventory."""

from __future__ import annotations
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from . import __version__
from .cox_lib import (
    CoxError,
    TRANSIENT_DIRS,
    fail,
    portable_segment,
    relative_path,
    walk_files,
    write_json,
)

FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXCLUDED_FILENAMES = {
    ".DS_Store",
    "cox-guides.zip",
    "cox_protocol_package_compiled.zip",
    "llm_agent_zip_skills_bundle.zip",
}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def excluded(path: Path) -> bool:
    return (
        path.name in EXCLUDED_FILENAMES
        or path.name == ".env"
        or path.name.startswith(".env.")
        or path.suffix in (".pyc", ".pyo", ".tgz")
        or any(p.endswith(".egg-info") for p in path.parts)
    )


def package_filename(summary) -> str:
    name = (
        summary.documents[summary.manifest_path].get("PackageName")
        or summary.documents[summary.manifest_path]["Slug"] + ".zip"
    )
    if not portable_segment(name):
        fail("PACKAGE_NAME", "PackageName must be a portable filename, not a path")
    return name if name.endswith(".zip") else name + ".zip"


def zip_write_bytes(archive, name, content, mode=0o644):
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIMESTAMP)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (stat.S_IFREG | mode) << 16
    archive.writestr(info, content)


def emit_package_archive(summary, build_root: Path, target_results) -> dict[str, Any]:
    archive_root = summary.documents[summary.manifest_path]["Slug"]
    if not portable_segment(archive_root):
        fail("PACKAGE_NAME", "Manifest Slug is a reserved archive directory name")
    entries = {}
    for reference in [summary.manifest_path, *summary.referenced_paths]:
        if any(
            part in TRANSIENT_DIRS
            for part in reference.relative_to(summary.project_root).parts
        ):
            fail(
                "PACKAGE_EXCLUDED",
                "Manifest explicitly references a transient directory",
                str(reference),
            )
        files = walk_files(reference) if reference.is_dir() else [reference]
        for source in files:
            if excluded(source):
                if source == reference:
                    fail(
                        "PACKAGE_EXCLUDED",
                        "Manifest explicitly references a transient or secret-like artifact",
                        str(source),
                    )
                continue
            if source.is_symlink() or not source.is_file():
                fail(
                    "PACKAGE_FILE",
                    "Package sources must be regular files without symlinks",
                    str(source),
                )
            rel = relative_path(summary.project_root, source)
            if rel == "package.manifest.json" or rel.startswith("build/"):
                fail("PACKAGE_RESERVED", "Source occupies a reserved archive path", rel)
            entries[rel] = (
                source.read_bytes(),
                0o755 if source.stat().st_mode & 0o111 else 0o644,
                "source",
            )
    # Only this staging directory is scanned, never the old destination directory.
    for path in sorted(build_root.rglob("*")):
        if path.is_file():
            rel = "build/" + path.relative_to(build_root).as_posix()
            entries[rel] = (path.read_bytes(), 0o644, "generated")
    records = [
        {
            "path": archive_root + "/" + rel,
            "source": rel,
            "kind": kind,
            "size": len(data),
            "sha256": sha256_bytes(data),
            "mode": mode,
        }
        for rel, (data, mode, kind) in sorted(entries.items())
    ]
    archive_path = build_root / "package" / package_filename(summary)
    manifest = {
        "generatedWith": f"cox {__version__}",
        "deterministic": True,
        "archiveRoot": archive_root,
        "projectName": summary.documents[summary.manifest_path]["ProjectName"],
        "packageName": archive_path.name,
        "fileCount": len(records),
        "files": records,
    }
    all_entries = {
        archive_root + "/" + rel: (data, mode)
        for rel, (data, mode, _) in entries.items()
    }
    all_entries[archive_root + "/package.manifest.json"] = (
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        0o644,
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, (content, mode) in sorted(all_entries.items()):
            zip_write_bytes(archive, name, content, mode)
    checksum = sha256_bytes(archive_path.read_bytes())
    manifest_path = archive_path.with_suffix(".manifest.json")
    write_json(
        manifest_path,
        {
            **manifest,
            "archive": {
                "path": archive_path.name,
                "size": archive_path.stat().st_size,
                "sha256": checksum,
            },
        },
    )
    return {
        "output_root": archive_path.parent,
        "archive": archive_path,
        "manifest": manifest_path,
        "file_count": len(all_entries),
        "sha256": checksum,
    }


def verify_archive(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(set(names)) != len(names):
                fail("ARCHIVE_DUPLICATE", "Archive contains duplicate names")
            for name in names:
                if (
                    any(part in ("", ".", "..") for part in name.split("/"))
                    or any(not portable_segment(part) for part in name.split("/"))
                    or any(c in name for c in '\\<>:"|?*')
                    or any(ord(c) < 32 for c in name)
                    or len(PurePosixPath(name).parts) < 2
                ):
                    fail("ARCHIVE_PATH", "Archive contains an invalid path", name)
            indexes = [
                name
                for name in names
                if len(PurePosixPath(name).parts) == 2
                and name.endswith("/package.manifest.json")
            ]
            if len(indexes) != 1:
                fail(
                    "ARCHIVE_MANIFEST",
                    "Expected one package.manifest.json at the archive root",
                )
            manifest = json.loads(archive.read(indexes[0]))
            root = manifest["archiveRoot"]
            if indexes[0] != root + "/package.manifest.json":
                fail("ARCHIVE_ROOT", "Manifest root differs from archive root")
            records = manifest["files"]
            if (
                not isinstance(root, str)
                or not isinstance(records, list)
                or any(not isinstance(record, dict) for record in records)
            ):
                fail("ARCHIVE_MANIFEST", "Invalid root or file inventory")
            for record in records:
                if (
                    not isinstance(record.get("path"), str)
                    or type(record.get("size")) is not int
                    or not isinstance(record.get("sha256"), str)
                    or record.get("mode") not in (0o644, 0o755)
                ):
                    fail("ARCHIVE_MANIFEST", "Invalid file record")
            if manifest["fileCount"] != len(records):
                fail("ARCHIVE_COUNT", "Manifest file count differs from records")
            declared = [record["path"] for record in records]
            if len(set(declared)) != len(declared) or set(names) != (
                set(declared) | set(indexes)
            ):
                fail(
                    "ARCHIVE_CONTENTS", "Archive entries differ from the file inventory"
                )
            for record in records:
                name = record["path"]
                if not name.startswith(root + "/"):
                    fail(
                        "ARCHIVE_ROOT",
                        "File is outside the declared archive root",
                        name,
                    )
                data = archive.read(name)
                if (
                    len(data) != record["size"]
                    or sha256_bytes(data) != record["sha256"]
                ):
                    fail(
                        "ARCHIVE_HASH",
                        "File does not match its size/SHA-256 record",
                        name,
                    )
                info = archive.getinfo(name)
                if stat.S_ISLNK(info.external_attr >> 16):
                    fail("ARCHIVE_SYMLINK", "Symlinks are not supported", name)
                if stat.S_IMODE(info.external_attr >> 16) != record["mode"]:
                    fail("ARCHIVE_MODE", "File permissions differ from inventory", name)
            return {
                "ok": True,
                "archive": str(path),
                "fileCount": len(records),
                "sha256": sha256_bytes(path.read_bytes()),
            }
    except (
        OSError,
        zipfile.BadZipFile,
        ValueError,
        KeyError,
        TypeError,
        RuntimeError,
    ) as exc:
        if isinstance(exc, CoxError):
            raise
        raise CoxError(f"Could not verify archive: {exc}") from exc
