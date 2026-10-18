from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import __version__
from .cox_lib import fail, portable_segment

if TYPE_CHECKING:
    from .cox_lib import ValidationSummary


def pascal_case(value: str) -> str:
    pieces = value.replace("-", "_").split("_")
    name = "".join(piece.capitalize() for piece in pieces if piece)
    return "Cox" + name if name[:1].isdigit() else name


def relative_import(from_dir: Path, target_dir: Path) -> str:
    import_path = os.path.relpath(target_dir, from_dir).replace(os.sep, "/")
    if import_path.startswith("."):
        return import_path
    return f"./{import_path}"


def document_for_instruction(
    summary: "ValidationSummary",
    instruction_path: str,
) -> dict[str, Any]:
    document_path = (summary.project_root / instruction_path).resolve()
    try:
        return summary.documents[document_path]
    except KeyError as exc:
        raise RuntimeError(
            f"Missing parsed COX document for {instruction_path}"
        ) from exc


def format_comment_block(lines: list[str]) -> str:
    body = "\n".join(
        " * " + line.replace("*/", "* /").replace("\r", " ").replace("\n", "\n * ")
        for line in lines
    )
    return f"/**\n{body}\n */"


def format_list(items: list[str]) -> str:
    if not items:
        return "none"
    if not isinstance(items, list):
        return json.dumps(items, ensure_ascii=True)
    return ", ".join(
        item if isinstance(item, str) else json.dumps(item, ensure_ascii=True)
        for item in items
    )


def evidence_comment_lines(document: dict[str, Any]) -> list[str]:
    return [
        f"{section}.{level}: {format_list(values)}"
        for section in ("EvidenceSummary", "Interactions")
        for level, values in document.get(section, {}).items()
    ]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def component_comment_lines(component: dict[str, Any]) -> list[str]:
    visual_style = component.get("VisualStyle", {})
    responsive = component.get("Responsive", {})
    interactions = component.get("Interactions", {})
    hints = component.get("ImplementationHints", [])
    return [
        f"COX component slug: {component.get('Slug', 'unknown')}",
        f"Role: {component.get('Role', 'unspecified')}",
        f"Token refs: {format_list(visual_style.get('Tokens', []))}",
        f"Desktop: {responsive.get('Desktop', 'unspecified')}",
        f"Tablet: {responsive.get('Tablet', 'unspecified')}",
        f"Mobile: {responsive.get('Mobile', 'unspecified')}",
        (f"Interaction notes: {format_list(interactions.get('Inferred', []))}"),
        f"Implementation hints: {format_list(hints)}",
    ] + evidence_comment_lines(component)


def page_comment_lines(page: dict[str, Any]) -> list[str]:
    layout = page.get("Layout", {})
    regions = page.get("VisibleStructure", {}).get("Regions", [])
    return [
        f"COX page slug: {page.get('Slug', 'unknown')}",
        f"Page type: {page.get('PageType', 'unspecified')}",
        f"Visible regions: {format_list(regions)}",
        f"Desktop layout: {layout.get('Desktop', 'unspecified')}",
        f"Tablet layout: {layout.get('Tablet', 'unspecified')}",
        f"Mobile layout: {layout.get('Mobile', 'unspecified')}",
    ] + evidence_comment_lines(page)


def render_component_stub(component: dict[str, Any]) -> str:
    component_name = pascal_case(component["Slug"])
    comment_block = format_comment_block(component_comment_lines(component))
    role = json.dumps(component.get("Role", "Component"))
    lines = [
        'import type { ReactNode } from "react";',
        "",
        comment_block,
        f"export interface {component_name}Props {{",
        "  children?: ReactNode;",
        "}",
        "",
        f"export function {component_name}({{",
        "  children,",
        f"}}: {component_name}Props) {{",
        "  return (",
        (f'    <section data-cox-slug="{component["Slug"]}" aria-label={{{role}}}>'),
        (
            "      {/* TODO: Replace this structural stub with the real UI "
            "implementation. */}"
        ),
        "      {children}",
        "    </section>",
        "  );",
        "}",
    ]
    return "\n".join(lines) + "\n"


def render_page_stub(
    page: dict[str, Any],
    component_entries: list[dict[str, Any]],
    react_root: Path,
) -> str:
    page_name = pascal_case(page["Slug"]) + "Page"
    page_dir = react_root / "pages" / page["ProjectName"] / pascal_case(page["Slug"])
    import_lines: list[str] = []
    render_lines: list[str] = []

    for component_entry in component_entries:
        component_name = pascal_case(component_entry["Slug"])
        component_dir = react_root / "components" / component_name
        import_path = relative_import(page_dir, component_dir)
        import_lines.append(f'import {{ {component_name} }} from "{import_path}";')
        render_lines.append(f"      <{component_name} />")

    comment_block = format_comment_block(page_comment_lines(page))
    imports = "\n".join(import_lines)
    rendered_components = "\n".join(render_lines)
    if not rendered_components:
        rendered_components = (
            "      {/* TODO: Wire child components from the COX page spec. */}"
        )

    return (
        f"{imports}\n\n"
        f"{comment_block}\n"
        f"export interface {page_name}Props {{}}\n\n"
        f"export function {page_name}(_: {page_name}Props) {{\n"
        "  return (\n"
        f'    <main data-cox-page="{page["Slug"]}">\n'
        f"{rendered_components}\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    )


def emit_react_stubs(
    summary: "ValidationSummary",
    build_root: Path,
) -> dict[str, Any]:
    symbols = {}
    for entry in summary.build_index["pages"]:
        payload = document_for_instruction(summary, entry["instruction"])
        project = payload["ProjectName"]
        if not portable_segment(project):
            fail(
                "REACT_PATH",
                "ProjectName must be a portable directory name for React output",
                entry["instruction"],
            )
        for symbol, source in [
            (pascal_case(entry["slug"]) + "Page", entry["instruction"])
        ] + [(pascal_case(c["slug"]), c["instruction"]) for c in entry["components"]]:
            if not portable_segment(symbol):
                fail(
                    "REACT_PATH",
                    f"Generated name {symbol} is a reserved filename",
                    source,
                )
            for declared in (symbol, symbol + "Props"):
                prior = symbols.setdefault(declared.casefold(), source)
                if prior != source:
                    fail(
                        "REACT_COLLISION",
                        f"Generated identifier {declared} collides with {prior}",
                        source,
                    )
    react_root = build_root / "react"
    component_records: dict[str, dict[str, Any]] = {}
    page_records: list[dict[str, Any]] = []

    for page_entry in summary.build_index["pages"]:
        page_payload = document_for_instruction(
            summary,
            page_entry["instruction"],
        )
        page_dir = (
            react_root
            / "pages"
            / page_payload["ProjectName"]
            / pascal_case(page_entry["slug"])
        )
        page_output = page_dir / "index.tsx"

        page_component_entries: list[dict[str, Any]] = []
        for component_entry in page_entry["components"]:
            slug = component_entry["slug"]
            component_payload = document_for_instruction(
                summary,
                component_entry["instruction"],
            )
            component_name = pascal_case(slug)
            component_dir = react_root / "components" / component_name
            component_output = component_dir / "index.tsx"
            if slug not in component_records:
                write_text(
                    component_output,
                    render_component_stub(component_payload),
                )
                component_records[slug] = {
                    "slug": slug,
                    "componentName": component_name,
                    "output": component_output.relative_to(react_root).as_posix(),
                }

            page_component_entries.append(
                {
                    "Slug": slug,
                    "ComponentName": component_name,
                }
            )

        write_text(
            page_output,
            render_page_stub(page_payload, page_component_entries, react_root),
        )
        page_records.append(
            {
                "projectName": page_payload["ProjectName"],
                "slug": page_payload["Slug"],
                "componentName": pascal_case(page_payload["Slug"]) + "Page",
                "output": page_output.relative_to(react_root).as_posix(),
                "children": page_component_entries,
            }
        )

    barrel_lines: list[str] = []
    for component in sorted(
        component_records.values(),
        key=lambda item: item["componentName"],
    ):
        component_name = component["componentName"]
        barrel_lines.append(
            (f'export {{ {component_name} }} from "./components/{component_name}";')
        )
        barrel_lines.append(
            (
                f"export type {{ {component_name}Props }} "
                f'from "./components/{component_name}";'
            )
        )

    for page in sorted(page_records, key=lambda item: item["componentName"]):
        page_component_name = page["componentName"]
        page_path = page["output"].removesuffix("/index.tsx")
        barrel_lines.append(f'export {{ {page_component_name} }} from "./{page_path}";')
        barrel_lines.append(
            (f'export type {{ {page_component_name}Props }} from "./{page_path}";')
        )

    write_text(react_root / "index.ts", "\n".join(barrel_lines) + "\n")

    manifest_payload = {
        "generatedWith": f"cox {__version__}",
        "target": "react",
        "components": sorted(
            component_records.values(),
            key=lambda item: item["componentName"],
        ),
        "pages": page_records,
    }
    write_text(
        react_root / "manifest.react.json",
        json.dumps(manifest_payload, indent=2, ensure_ascii=True) + "\n",
    )

    return {
        "output_root": react_root,
        "component_count": len(component_records),
        "page_count": len(page_records),
        "manifest": react_root / "manifest.react.json",
    }
