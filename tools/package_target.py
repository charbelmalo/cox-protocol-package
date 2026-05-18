from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

from . import __version__
from .cox_lib import relative_path


if TYPE_CHECKING:
    from .cox_lib import ValidationSummary


FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tgz"}
EXCLUDED_FILENAMES = {
    ".DS_Store",
    "cox-guides.zip",
    "cox_protocol_package_compiled.zip",
    "llm_agent_zip_skills_bundle.zip",
}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_filename(summary: "ValidationSummary") -> str:
    manifest = summary.documents[summary.manifest_path]
    raw_name = str(manifest.get("PackageName") or "cox_protocol_package.zip")
    file_name = Path(raw_name).name
    if not file_name.endswith(".zip"):
        file_name = f"{file_name}.zip"
    if file_name == ".zip":
        return "cox_protocol_package.zip"
    return file_name


def is_safe_project_file(
    path: Path,
    project_root: Path,
    package_output: Path,
) -> bool:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(project_root.resolve())
    except ValueError:
        return False

    if resolved == package_output.resolve():
        return False
    if relative.parts[:2] == ("build", "package"):
        return False
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if relative.name in EXCLUDED_FILENAMES:
        return False
    if relative.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if path.is_dir():
        for child in path.rglob("*"):
            if child.is_file() and not child.is_symlink():
                yield child


def collect_package_files(
    summary: "ValidationSummary",
    target_results: dict[str, dict[str, Any]],
    package_output: Path,
) -> list[Path]:
    candidates: list[Path] = [summary.manifest_path, *summary.referenced_paths]

    for target_name, result in target_results.items():
        if target_name == "package":
            continue
        for key in ("output_root", "manifest"):
            value = result.get(key)
            if isinstance(value, Path):
                candidates.append(value)

    files_by_relative_path: dict[str, Path] = {}
    for candidate in candidates:
        for file_path in iter_files(candidate):
            if not is_safe_project_file(
                file_path,
                summary.project_root,
                package_output,
            ):
                continue
            relative = relative_path(summary.project_root, file_path)
            files_by_relative_path[relative] = file_path.resolve()

    return [
        files_by_relative_path[key]
        for key in sorted(files_by_relative_path)
    ]


def zip_write_bytes(
    archive: zipfile.ZipFile,
    archive_path: str,
    content: bytes,
) -> None:
    info = zipfile.ZipInfo(archive_path, FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, content)


def emit_package_archive(
    summary: "ValidationSummary",
    build_root: Path,
    target_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    output_root = build_root / "package"
    output_root.mkdir(parents=True, exist_ok=True)

    archive_path = output_root / package_filename(summary)
    source_files = collect_package_files(
        summary,
        target_results,
        archive_path,
    )
    archive_root = summary.project_root.name

    file_records = []
    for source_file in source_files:
        relative = relative_path(summary.project_root, source_file)
        file_records.append(
            {
                "path": f"{archive_root}/{relative}",
                "source": relative,
                "size": source_file.stat().st_size,
                "sha256": sha256_file(source_file),
            }
        )

    package_manifest = {
        "generatedWith": f"cox {__version__}",
        "deterministic": True,
        "archiveRoot": archive_root,
        "projectName": summary.documents[summary.manifest_path].get(
            "ProjectName"
        ),
        "packageName": archive_path.name,
        "fileCount": len(file_records),
        "files": file_records,
    }
    manifest_bytes = (
        json.dumps(package_manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    with zipfile.ZipFile(archive_path, "w") as archive:
        for source_file, file_record in zip(source_files, file_records):
            zip_write_bytes(
                archive,
                str(file_record["path"]),
                source_file.read_bytes(),
            )
        zip_write_bytes(
            archive,
            f"{archive_root}/package.manifest.json",
            manifest_bytes,
        )

    archive_bytes = archive_path.read_bytes()
    archive_sha256 = sha256_bytes(archive_bytes)
    disk_manifest = {
        **package_manifest,
        "archive": {
            "path": relative_path(summary.project_root, archive_path),
            "size": archive_path.stat().st_size,
            "sha256": archive_sha256,
        },
    }
    manifest_path = output_root / f"{archive_path.stem}.manifest.json"
    manifest_path.write_text(
        json.dumps(disk_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "output_root": output_root,
        "archive": archive_path,
        "manifest": manifest_path,
        "file_count": len(file_records) + 1,
        "sha256": archive_sha256,
    }
