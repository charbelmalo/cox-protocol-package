# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]


SCHEMA_FILENAMES = {
    "cox.manifest.v1": "cox.manifest.v1.schema.json",
    "cox.page.v1": "cox.page.v1.schema.json",
    "cox.component.v1": "cox.component.v1.schema.json",
    "cox.protocol.v1": "cox.protocol.v1.schema.json",
    "cox.crop_metadata.v1": "cox.crop_metadata.v1.schema.json",
}


class CoxError(RuntimeError):
    """Raised when COX validation or compilation fails."""


@dataclass(slots=True)
class ValidationSummary:
    project_root: Path
    manifest_path: Path
    documents: dict[Path, dict[str, Any]]
    referenced_paths: list[Path]
    warnings: list[str]
    build_index: dict[str, Any]


def resolve_project_root(target: Path) -> tuple[Path, Path]:
    resolved_target = target.resolve()
    search_root = (
        resolved_target
        if resolved_target.is_dir()
        else resolved_target.parent
    )

    direct_manifest = search_root / "manifest.cox"
    if direct_manifest.exists():
        return search_root, direct_manifest

    for candidate_root in [search_root, *search_root.parents]:
        manifest_path = candidate_root / "manifest.cox"
        if manifest_path.exists():
            return candidate_root, manifest_path

    raise CoxError(f"Could not locate manifest.cox from {target}")


def read_yaml_document(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CoxError(f"{path}: file is not valid UTF-8") from exc

    try:
        document = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise CoxError(f"{path}: YAML parsing failed: {exc}") from exc

    if not isinstance(document, dict):
        raise CoxError(f"{path}: top-level COX document must be a mapping")

    return document


def read_json_document(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CoxError(f"{path}: JSON parsing failed: {exc}") from exc


def load_schema(schema_dir: Path, schema_name: str) -> dict[str, Any]:
    schema_file = SCHEMA_FILENAMES.get(schema_name)
    if schema_file is None:
        raise CoxError(f"Unknown COX schema id: {schema_name}")

    schema_path = schema_dir / schema_file
    if not schema_path.exists():
        raise CoxError(f"Schema file is missing: {schema_path}")

    return read_json_document(schema_path)


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def unique_paths(paths: list[Path]) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(resolved)
    return ordered


def validate_against_schema(
    document: dict[str, Any],
    path: Path,
    schema_dir: Path,
) -> list[str]:
    schema_name = document.get("Schema")
    if not isinstance(schema_name, str) or not schema_name:
        return [f"{path}: missing Schema field"]

    schema = load_schema(schema_dir, schema_name)
    validator = Draft202012Validator(schema)
    issues: list[str] = []

    sorted_errors = sorted(
        validator.iter_errors(document),
        key=lambda item: list(item.absolute_path),
    )
    for error in sorted_errors:
        location = ".".join(str(part) for part in error.absolute_path)
        prefix = f"{path}: {location}" if location else str(path)
        issues.append(f"{prefix}: {error.message}")

    return issues


def build_manifest_index(
    manifest: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    reference_docs = [
        project_root / path for path in manifest.get("ReferenceDocs", [])
    ]
    protocol_docs = [
        project_root / path for path in manifest.get("ProtocolDocs", [])
    ]
    schema_files = [
        project_root / path for path in manifest.get("Schemas", [])
    ]
    tooling_files = [
        project_root / path for path in manifest.get("ToolingFiles", [])
    ]

    page_entries: list[dict[str, Any]] = []
    cox_documents = protocol_docs.copy()
    referenced_paths = (
        reference_docs + protocol_docs + schema_files + tooling_files
    )

    for page in manifest.get("Pages", []):
        page_instruction = project_root / page["PageInstruction"]
        page_screenshot = project_root / page["PageScreenshotPlaceholder"]
        referenced_paths.extend([page_instruction, page_screenshot])
        cox_documents.append(page_instruction)

        component_entries: list[dict[str, Any]] = []
        for component in page.get("Components", []):
            component_instruction = (
                project_root / component["ComponentInstruction"]
            )
            component_screenshot = (
                project_root / component["ComponentScreenshotPlaceholder"]
            )
            referenced_paths.extend(
                [component_instruction, component_screenshot]
            )
            cox_documents.append(component_instruction)
            component_entries.append(
                {
                    "slug": component["Slug"],
                    "folder": component["Folder"],
                    "instruction": relative_path(
                        project_root,
                        component_instruction,
                    ),
                    "screenshot": relative_path(
                        project_root,
                        component_screenshot,
                    ),
                }
            )

        page_entries.append(
            {
                "pageName": page["PageName"],
                "slug": page["Slug"],
                "folder": page["Folder"],
                "instruction": relative_path(project_root, page_instruction),
                "screenshot": relative_path(project_root, page_screenshot),
                "components": component_entries,
            }
        )

    return {
        "reference_docs": [
            relative_path(project_root, path) for path in reference_docs
        ],
        "protocol_docs": [
            relative_path(project_root, path) for path in protocol_docs
        ],
        "schema_files": [
            relative_path(project_root, path) for path in schema_files
        ],
        "tooling_files": [
            relative_path(project_root, path) for path in tooling_files
        ],
        "pages": page_entries,
        "cox_documents": unique_paths(
            [project_root / "manifest.cox", *cox_documents]
        ),
        "referenced_paths": unique_paths(referenced_paths),
    }


def validate_project(target: Path) -> ValidationSummary:
    project_root, manifest_path = resolve_project_root(target)
    schema_dir = project_root / "schemas"
    manifest = read_yaml_document(manifest_path)

    issues = validate_against_schema(manifest, manifest_path, schema_dir)
    manifest_index = build_manifest_index(manifest, project_root)

    missing_paths = [
        path
        for path in manifest_index["referenced_paths"]
        if not path.exists()
    ]
    if missing_paths:
        missing_lines = [
            f"Missing referenced path: {relative_path(project_root, path)}"
            for path in missing_paths
        ]
        missing_text = "\n".join(missing_lines)
        issues.append(missing_text)

    documents: dict[Path, dict[str, Any]] = {manifest_path.resolve(): manifest}
    for document_path in manifest_index["cox_documents"]:
        document = read_yaml_document(document_path)
        documents[document_path.resolve()] = document
        issues.extend(
            validate_against_schema(document, document_path, schema_dir)
        )

    discovered_cox_files = [
        path.resolve()
        for path in project_root.rglob("*.cox")
        if "build" not in path.parts
    ]
    referenced_cox_files = set(manifest_index["cox_documents"])
    unreferenced_files = [
        path
        for path in discovered_cox_files
        if path not in referenced_cox_files
    ]
    warnings: list[str] = []
    if unreferenced_files:
        unreferenced_text = ", ".join(
            relative_path(project_root, path)
            for path in sorted(unreferenced_files)
        )
        warnings.append(
            "Unreferenced COX files: " + unreferenced_text
        )

    if issues:
        raise CoxError("\n".join(issues))

    return ValidationSummary(
        project_root=project_root,
        manifest_path=manifest_path.resolve(),
        documents=documents,
        referenced_paths=manifest_index["referenced_paths"],
        warnings=warnings,
        build_index=manifest_index,
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    path.write_text(serialized, encoding="utf-8")


def build_report(summary: ValidationSummary, build_root: Path) -> str:
    warning_lines = summary.warnings or ["none"]
    report_lines = [
        "CompiledVerificationReport:",
        '  CoxVersion: "1.0"',
        f'  ProjectRoot: "{summary.project_root.as_posix()}"',
        (
            "  Manifest: "
            f'"{relative_path(summary.project_root, summary.manifest_path)}"'
        ),
        f'  ValidatedDocuments: {len(summary.documents)}',
        f'  NormalizedOutputRoot: "{(build_root / "normalized").as_posix()}"',
        (
            "  CompiledManifest: "
            f'"{(build_root / "manifest.compiled.json").as_posix()}"'
        ),
        f'  ReferencedPathsChecked: {len(summary.referenced_paths)}',
        "  Warnings:",
    ]
    report_lines.extend(f'    - "{line}"' for line in warning_lines)
    report_lines.extend(
        [
            "  Outputs:",
            (
                "    VerificationReport: "
                f'"{(
                    build_root / "reports" / "verification_report.txt"
                ).as_posix()}"'
            ),
            (
                "    ManifestCompiledJson: "
                f'"{(build_root / "manifest.compiled.json").as_posix()}"'
            ),
            (
                "    NormalizedDirectory: "
                f'"{(build_root / "normalized").as_posix()}"'
            ),
        ]
    )
    return "\n".join(report_lines) + "\n"


def compile_project(target: Path, out_dir: Path) -> dict[str, Any]:
    summary = validate_project(target)
    build_root = (
        out_dir if out_dir.is_absolute() else summary.project_root / out_dir
    )
    normalized_root = build_root / "normalized"
    reports_root = build_root / "reports"

    for document_path, payload in summary.documents.items():
        if document_path == summary.manifest_path:
            continue
        output_path = normalized_root / document_path.relative_to(
            summary.project_root
        )
        write_json(output_path.with_suffix(".json"), payload)

    manifest_payload = {
        "compiledWith": "cox 1.0.0",
        "mimeType": "application/vnd.cox+yaml",
        "manifest": summary.documents[summary.manifest_path],
        "resolvedFiles": {
            "referenceDocs": summary.build_index["reference_docs"],
            "protocolDocs": summary.build_index["protocol_docs"],
            "schemaFiles": summary.build_index["schema_files"],
            "toolingFiles": summary.build_index["tooling_files"],
            "pages": summary.build_index["pages"],
        },
        "warnings": summary.warnings,
    }
    write_json(build_root / "manifest.compiled.json", manifest_payload)

    reports_root.mkdir(parents=True, exist_ok=True)
    report_path = reports_root / "verification_report.txt"
    report_path.write_text(build_report(summary, build_root), encoding="utf-8")

    return {
        "build_root": build_root,
        "normalized_count": len(summary.documents) - 1,
        "compiled_manifest": build_root / "manifest.compiled.json",
        "report": report_path,
        "warnings": summary.warnings,
    }
