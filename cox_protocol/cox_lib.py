"""COX v1 parsing, canonical validation and project reference resolution."""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

import yaml
from jsonschema import Draft202012Validator

SCHEMA_FILENAMES = {
    "cox.manifest.v1": "cox.manifest.v1.schema.json",
    "cox.page.v1": "cox.page.v1.schema.json",
    "cox.component.v1": "cox.component.v1.schema.json",
    "cox.protocol.v1": "cox.protocol.v1.schema.json",
    "cox.crop_metadata.v1": "cox.crop_metadata.v1.schema.json",
}
SUPPORTED_COMPILE_TARGETS = ("json", "react", "package")
TRANSIENT_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}


def portable_segment(value: str) -> bool:
    reserved = {"con", "prn", "aux", "nul"} | {
        f"{prefix}{i}" for prefix in ("com", "lpt") for i in range(1, 10)
    }
    return (
        bool(value.strip())
        and not value.endswith((" ", "."))
        and value.split(".")[0].casefold() not in reserved
        and not any(c in value for c in '/\\<>:"|?*')
        and not any(ord(c) < 32 for c in value)
    )


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    path: str = ""
    location: str = ""

    def __str__(self) -> str:
        label = ": ".join(part for part in (self.path, self.location) if part)
        return f"{label}: {self.message}" if label else self.message


class CoxError(RuntimeError):
    def __init__(self, issues: str | list[Diagnostic]):
        self.issues = (
            [Diagnostic("COX_ERROR", issues)] if isinstance(issues, str) else issues
        )
        super().__init__("\n".join(str(issue) for issue in self.issues))

    def as_dict(self) -> dict[str, Any]:
        return {"ok": False, "errors": [asdict(issue) for issue in self.issues]}


def fail(code: str, message: str, path: str = "", location: str = "") -> None:
    raise CoxError([Diagnostic(code, message, path, location)])


@dataclass
class ValidationSummary:
    project_root: Path
    manifest_path: Path
    documents: dict[Path, dict[str, Any]]
    referenced_paths: list[Path]
    warnings: list[str]
    build_index: dict[str, Any]


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def format_report_path(root: Path, path: Path) -> str:
    try:
        return relative_path(root, path)
    except ValueError:
        return path.resolve().as_posix()


def resolve_project_root(target: Path) -> tuple[Path, Path]:
    target = target.resolve()
    if not target.exists():
        fail("PROJECT_MISSING", "Project path does not exist", str(target))
    folder = target if target.is_dir() else target.parent
    for candidate in (folder, *folder.parents):
        manifest = candidate / "manifest.cox"
        if manifest.is_file():
            if manifest.is_symlink():
                fail(
                    "PATH_SYMLINK", "manifest.cox must be a regular file", str(manifest)
                )
            return candidate, manifest
    fail("MANIFEST_MISSING", "Could not locate manifest.cox", str(target))


class CoxLoader(yaml.SafeLoader):
    """Reject ambiguous keys/aliases rather than silently changing the contract."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise yaml.YAMLError("YAML aliases are not supported; use explicit values")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise yaml.YAMLError("Mapping keys must be strings")
            if key in mapping:
                raise yaml.YAMLError(
                    f"Duplicate mapping key {key!r} at line {key_node.start_mark.line + 1}"
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def check_json_value(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("Mapping keys must be strings")
            check_json_value(child)
    elif isinstance(value, list):
        for child in value:
            check_json_value(child)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite numbers are not supported")
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError(
            f"{type(value).__name__} is not a JSON-compatible value; quote dates and other text"
        )


def read_yaml_document(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
        document = yaml.load(content, Loader=CoxLoader)
        if not isinstance(document, dict):
            fail("DOCUMENT_TYPE", "Top-level COX document must be a mapping", str(path))
        check_json_value(document)
        return document
    except UnicodeDecodeError as exc:
        raise CoxError(
            [Diagnostic("UTF8_INVALID", "File is not valid UTF-8", str(path))]
        ) from exc
    except OSError as exc:
        raise CoxError([Diagnostic("FILE_UNREADABLE", str(exc), str(path))]) from exc
    except (yaml.YAMLError, ValueError, RecursionError) as exc:
        raise CoxError([Diagnostic("YAML_INVALID", str(exc), str(path))]) from exc


def read_json_document(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        check_json_value(value)
        return value
    except (OSError, ValueError) as exc:
        raise CoxError([Diagnostic("JSON_INVALID", str(exc), str(path))]) from exc


def load_schema(schema_dir: Path | None, schema_name: str) -> dict[str, Any]:
    """Canonical schemas are part of the compiler; a project cannot redefine v1."""
    filename = SCHEMA_FILENAMES.get(schema_name)
    if filename is None:
        fail("SCHEMA_UNKNOWN", f"Unknown COX schema id: {schema_name!r}")
    schema = read_json_document(Path(__file__).parent / "schemas" / filename)
    Draft202012Validator.check_schema(schema)
    return schema


def schema_issues(document: dict[str, Any], path: Path) -> list[Diagnostic]:
    schema_name = document.get("Schema")
    if not isinstance(schema_name, str) or schema_name not in SCHEMA_FILENAMES:
        return [
            Diagnostic(
                "SCHEMA_UNKNOWN",
                f"Unknown or missing Schema: {schema_name!r}",
                str(path),
                "Schema",
            )
        ]
    errors = Draft202012Validator(load_schema(None, schema_name)).iter_errors(document)
    return [
        Diagnostic(
            "SCHEMA_INVALID",
            error.message,
            str(path),
            ".".join(map(str, error.absolute_path)),
        )
        for error in sorted(
            errors, key=lambda error: tuple(map(str, error.absolute_path))
        )
    ]


def validate_against_schema(document, path, schema_dir=None) -> list[str]:
    return [str(issue) for issue in schema_issues(document, path)]


def safe_project_path(
    root: Path,
    raw: str,
    label: str,
    kind: str | None = None,
    *,
    allow_parent: bool = False,
) -> Path:
    if (
        not raw
        or "\\" in raw
        or any(c in raw for c in '\x00<>:"|?*')
        or any(ord(c) < 32 for c in raw)
        or raw.startswith("/")
        or (not allow_parent and ".." in raw.split("/"))
        or raw.rstrip("/") in ("", ".")
    ):
        fail(
            "PATH_INVALID",
            "Use a non-empty project-relative POSIX path without parent traversal",
            label,
        )
    if any(
        not portable_segment(part)
        for part in raw.split("/")
        if part not in ("", ".", "..")
    ):
        fail("PATH_INVALID", "Reference contains a non-portable filename", label)
    path = root / PurePosixPath(raw)
    for ancestor in (path, *path.parents):
        if ancestor == root:
            break
        if ancestor.is_symlink():
            fail(
                "PATH_SYMLINK", "Symlink references are not portable COX inputs", label
            )
    try:
        path.resolve().relative_to(root)
    except ValueError:
        fail("PATH_OUTSIDE_PROJECT", "Reference leaves the project root", label)
    if not path.exists():
        fail("REFERENCE_MISSING", f"Referenced path does not exist: {raw}", label)
    if kind == "file" and not path.is_file():
        fail("REFERENCE_TYPE", f"Expected a file: {raw}", label)
    if kind == "directory" and not path.is_dir():
        fail("REFERENCE_TYPE", f"Expected a directory: {raw}", label)
    return path.resolve()


def unique_paths(paths: list[Path]) -> list[Path]:
    return sorted(set(path.resolve() for path in paths))


def walk_files(root: Path, skip_nested_projects: bool = False):
    """Stable traversal, without caches, symlinks, or nested independent projects."""
    for folder, dirs, files in os.walk(root, followlinks=False):
        base = Path(folder)
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in TRANSIENT_DIRS
            and not d.endswith(".egg-info")
            and not (base / d).is_symlink()
            and not (skip_nested_projects and (base / d / "manifest.cox").is_file())
        )
        if base != root and (base / ".cox-build.json").exists():
            dirs[:] = []
            continue
        for name in sorted(files):
            yield base / name


def build_manifest_index(
    manifest: dict[str, Any], project_root: Path
) -> dict[str, Any]:
    index: dict[str, Any] = {}
    refs, docs = [], [project_root / "manifest.cox"]
    for key, field in [
        ("reference_docs", "ReferenceDocs"),
        ("guide_docs", "GuideDocs"),
        ("protocol_docs", "ProtocolDocs"),
        ("skill_bundles", "SkillBundles"),
        ("schema_files", "Schemas"),
        ("tooling_files", "ToolingFiles"),
    ]:
        paths = [
            safe_project_path(project_root, raw, f"manifest.cox: {field}[{i}]")
            for i, raw in enumerate(manifest.get(field, []))
        ]
        index[key] = [relative_path(project_root, path) for path in paths]
        refs.extend(paths)
        if field in ("ProtocolDocs", "GuideDocs", "SkillBundles"):
            for path in paths:
                candidates = walk_files(path) if path.is_dir() else [path]
                docs.extend(
                    safe_project_path(
                        project_root,
                        p.relative_to(project_root).as_posix(),
                        field,
                        "file",
                    )
                    for p in candidates
                    if p.suffix == ".cox"
                )
        if field == "ProtocolDocs" and any(
            p.suffix != ".cox" or not p.is_file() for p in paths
        ):
            fail(
                "REFERENCE_TYPE",
                "ProtocolDocs entries must be .cox files",
                "manifest.cox",
            )
    index["pages"] = []
    for i, page in enumerate(manifest["Pages"]):
        label = f"manifest.cox: Pages[{i}]"
        folder = safe_project_path(
            project_root, page["Folder"], label + ".Folder", "directory"
        )
        instruction = safe_project_path(
            project_root, page["PageInstruction"], label + ".PageInstruction", "file"
        )
        shot = safe_project_path(
            project_root,
            page["PageScreenshotPlaceholder"],
            label + ".PageScreenshotPlaceholder",
            "file",
        )
        if not instruction.is_relative_to(folder) or not shot.is_relative_to(folder):
            fail(
                "BINDING_FOLDER",
                "Page instruction and evidence must be within its Folder",
                label,
            )
        refs.extend([instruction, shot])
        docs.append(instruction)
        entry = {
            "pageName": page["PageName"],
            "slug": page["Slug"],
            "folder": relative_path(project_root, folder),
            "instruction": relative_path(project_root, instruction),
            "screenshot": relative_path(project_root, shot),
            "components": [],
        }
        for j, component in enumerate(page["Components"]):
            clabel = f"{label}.Components[{j}]"
            cfolder = safe_project_path(
                project_root, component["Folder"], clabel + ".Folder", "directory"
            )
            cinstruction = safe_project_path(
                project_root,
                component["ComponentInstruction"],
                clabel + ".ComponentInstruction",
                "file",
            )
            cshot = safe_project_path(
                project_root,
                component["ComponentScreenshotPlaceholder"],
                clabel + ".ComponentScreenshotPlaceholder",
                "file",
            )
            if not cinstruction.is_relative_to(cfolder) or not cshot.is_relative_to(
                cfolder
            ):
                fail(
                    "BINDING_FOLDER",
                    "Component instruction and evidence must be within its Folder",
                    clabel,
                )
            refs.extend([cinstruction, cshot])
            docs.append(cinstruction)
            entry["components"].append(
                {
                    "slug": component["Slug"],
                    "folder": relative_path(project_root, cfolder),
                    "instruction": relative_path(project_root, cinstruction),
                    "screenshot": relative_path(project_root, cshot),
                }
            )
        index["pages"].append(entry)
    index["referenced_paths"] = unique_paths(refs)
    index["cox_documents"] = unique_paths(docs)
    return index


def validate_bindings(manifest, index, documents, root):
    errors = []
    page_slugs, component_slugs = set(), {}
    for page in index["pages"]:
        doc = documents[root / page["instruction"]]
        expected = {
            "FileType": "page_spec",
            "Slug": page["slug"],
            "PageName": page["pageName"],
            "ProjectName": manifest["ProjectName"],
        }
        for key, value in expected.items():
            if doc.get(key) != value:
                errors.append(
                    Diagnostic(
                        "BINDING_MISMATCH",
                        f"Expected {value!r}, got {doc.get(key)!r}",
                        page["instruction"],
                        key,
                    )
                )
        if page["slug"] in page_slugs:
            errors.append(
                Diagnostic(
                    "SLUG_DUPLICATE",
                    f"Duplicate page slug {page['slug']}",
                    "manifest.cox",
                )
            )
        page_slugs.add(page["slug"])
        children = doc.get("Children", {}).get("Components", [])
        bound = {c["slug"]: c for c in page["components"]}
        if len(bound) != len(page["components"]) or len(
            {c["Slug"] for c in children}
        ) != len(children):
            errors.append(
                Diagnostic(
                    "SLUG_DUPLICATE",
                    "Duplicate component binding within page",
                    page["instruction"],
                )
            )
        if {c["Slug"] for c in children} != set(bound):
            errors.append(
                Diagnostic(
                    "BINDING_MISMATCH",
                    "Children.Components must match the manifest component slugs",
                    page["instruction"],
                )
            )
        for child in children:
            if child["Slug"] in bound:
                child_path = Path(page["instruction"]).parent / child["Folder"]
                # Child folders are relative to the page document, not the manifest.
                try:
                    resolved = safe_project_path(
                        root,
                        child_path.as_posix(),
                        page["instruction"] + ": Children.Folder",
                        "directory",
                        allow_parent=True,
                    )
                    if relative_path(root, resolved) != bound[child["Slug"]]["folder"]:
                        errors.append(
                            Diagnostic(
                                "BINDING_FOLDER",
                                "Child folder differs from manifest binding",
                                page["instruction"],
                                child["Slug"],
                            )
                        )
                except CoxError as exc:
                    errors.extend(exc.issues)
        for component in page["components"]:
            path = root / component["instruction"]
            payload = documents[path]
            for key, value in {
                "FileType": "component_spec",
                "Slug": component["slug"],
            }.items():
                if payload.get(key) != value:
                    errors.append(
                        Diagnostic(
                            "BINDING_MISMATCH",
                            f"Expected {value!r}, got {payload.get(key)!r}",
                            component["instruction"],
                            key,
                        )
                    )
            prior = component_slugs.setdefault(component["slug"], path)
            if prior != path:
                errors.append(
                    Diagnostic(
                        "SLUG_DUPLICATE",
                        "Same component slug refers to different source files",
                        component["instruction"],
                        component["slug"],
                    )
                )
    if errors:
        raise CoxError(errors)


def validate_project(target: Path) -> ValidationSummary:
    root, manifest_path = resolve_project_root(target)
    manifest = read_yaml_document(manifest_path)
    issues = schema_issues(manifest, manifest_path)
    if manifest.get("Schema") != "cox.manifest.v1":
        issues.append(
            Diagnostic(
                "MANIFEST_TYPE",
                "manifest.cox must use cox.manifest.v1",
                str(manifest_path),
            )
        )
    if issues:
        raise CoxError(issues)
    index = build_manifest_index(manifest, root)
    documents = {manifest_path: manifest}
    for path in index["cox_documents"]:
        if path == manifest_path:
            continue
        try:
            if path.suffix != ".cox":
                fail(
                    "DOCUMENT_EXTENSION",
                    "COX instructions must use the .cox extension",
                    str(path),
                )
            doc = read_yaml_document(path)
            documents[path] = doc
            issues.extend(schema_issues(doc, path))
        except CoxError as exc:
            issues.extend(exc.issues)
    if issues:
        raise CoxError(issues)
    validate_bindings(manifest, index, documents, root)
    for raw in index["protocol_docs"]:
        if documents[root / raw].get("FileType") != "protocol_doc":
            fail(
                "BINDING_MISMATCH",
                "ProtocolDocs must reference protocol_doc documents",
                raw,
            )
    unreferenced = [
        relative_path(root, p)
        for p in walk_files(root, skip_nested_projects=True)
        if p.suffix == ".cox" and p.resolve() not in documents and not p.is_symlink()
    ]
    warnings = (
        ["Unreferenced COX files: " + ", ".join(sorted(unreferenced))]
        if unreferenced
        else []
    )
    return ValidationSummary(
        root, manifest_path, documents, index["referenced_paths"], warnings, index
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def normalize_compile_targets(targets: Sequence[str] | None) -> list[str]:
    expanded = []
    for raw in targets or ["json"]:
        expanded.extend(part.strip().lower() for part in raw.split(",") if part.strip())
    if "all" in expanded:
        expanded = [t for t in expanded if t != "all"] + list(SUPPORTED_COMPILE_TARGETS)
    unknown = set(expanded) - set(SUPPORTED_COMPILE_TARGETS)
    if unknown:
        fail(
            "TARGET_UNKNOWN",
            "Unsupported compile target(s): " + ", ".join(sorted(unknown)),
        )
    return [
        target
        for target in SUPPORTED_COMPILE_TARGETS
        if target in (expanded or ["json"])
    ]


def compile_project(
    target: Path,
    out_dir: Path,
    targets: Sequence[str] | None = None,
    strict: bool = False,
):
    from .compiler import compile_project as compile_impl

    return compile_impl(target, out_dir, targets, strict)
