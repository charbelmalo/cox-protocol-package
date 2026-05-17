# COX Protocol Package

COX is a versioned, YAML-compatible file format for UI reconstruction, evidence tracking, component binding, implementation guidance, and agent-readable design specifications.

This repository now treats `.cox` as a real format surface rather than renamed text files. COX v1.0 includes:

- a formal file format specification
- versioned headers on `.cox` documents
- JSON Schemas for validation
- a manifest-driven validator/compiler CLI
- normalized JSON build output
- minimal VS Code language support

## COX v1.0

- Extension: `.cox`
- MIME type: `application/vnd.cox+yaml`
- Encoding: `UTF-8`
- Syntax base: `YAML-compatible structured text`
- Entry point: `manifest.cox`

Every `.cox` document starts with a common header:

```yaml
CoxVersion: "1.0"
FileType: "component_spec"
Slug: "projects_grid_cards"
Schema: "cox.component.v1"
```

## Repository Contents

- `COX_FILE_FORMAT_SPECIFICATION_v1.0.md`: formal format rules for COX v1.0
- `manifest.cox`: manifest entrypoint for validation and compilation
- `schemas/`: JSON Schemas for manifest, page, component, protocol, and crop metadata documents
- `tools/`: Python validator/compiler package and CLI
- `editor-support/vscode/`: minimal VS Code language registration for `.cox`
- `LocalAppManager/`: example manifest-driven project content
- `templates/`: versioned starter templates for page, component, and crop metadata files

## Commands

Install the toolchain:

```bash
python -m pip install -e .
```

Validate a COX project:

```bash
cox validate .
```

Compile a COX project to normalized JSON:

```bash
cox compile . --out build
```

## Build Output

Compilation emits:

```text
build/
  manifest.compiled.json
  normalized/
  reports/
    verification_report.txt
```

## Example Layout

```text
LocalAppManager/
  Dashboard/
    dashboard.cox
    dashboard_screenshot.placeholder.txt
    left_navigation_sidebar/
      left_navigation_sidebar.cox
      left_navigation_sidebar_screenshot.placeholder.txt
    top_header_stats_bar/
      top_header_stats_bar.cox
      top_header_stats_bar_screenshot.placeholder.txt
    projects_grid_cards/
      projects_grid_cards.cox
      projects_grid_cards_screenshot.placeholder.txt
    analytics_sidebar_panels/
      analytics_sidebar_panels.cox
      analytics_sidebar_panels_screenshot.placeholder.txt
```

The formal COX rules live in `COX_FILE_FORMAT_SPECIFICATION_v1.0.md`, and the executable contract lives in the schema files under `schemas/`.
