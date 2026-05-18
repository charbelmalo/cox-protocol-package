# COX Protocol Package

COX is a versioned, YAML-compatible file format for UI reconstruction, evidence tracking, component binding, implementation guidance, and agent-readable design specifications.

This repository now treats `.cox` as a real format surface rather than renamed text files. COX v1.0 includes:

- a formal file format specification
- versioned headers on `.cox` documents
- JSON Schemas for validation
- a manifest-driven validator/compiler CLI
- normalized JSON build output
- deterministic package ZIP output
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
- `protocols/`: shared protocol documents referenced by the manifest
- `guides/`: package guides, including imported archive audit notes and NPM installation instructions
- `skills/`: LLM-agent skill bundles imported from `llm_agent_zip_skills_bundle.zip`
- `schemas/`: JSON Schemas for manifest, page, component, protocol, and crop metadata documents
- `tools/`: Python validator/compiler package and CLI
- `bin/`: NPM wrapper that delegates to the Python COX CLI
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

Compile React stubs from the same normalized COX document model:

```bash
cox compile . --target react --out build
```

Compile multiple targets in one pass:

```bash
cox compile . --target json --target react --target package --out build
```

The `package` target emits a deterministic ZIP archive and package manifest under `build/package/`. The archive uses sorted paths, fixed ZIP timestamps, project-relative names, SHA-256 file records, and excludes transient local artifacts such as `.venv`, `.mypy_cache`, `node_modules`, `*.egg-info`, raw intake ZIPs, and `build/package` itself.

## Build Output

Compilation emits:

```text
build/
  manifest.compiled.json
  normalized/
  reports/
    verification_report.txt
  package/
    cox_protocol_package_corrected.zip
    cox_protocol_package_corrected.manifest.json
```

When the `react` target is requested, compilation also emits:

```text
build/
  react/
    components/
    pages/
    index.ts
    manifest.react.json
```

The React target is intentionally stub-oriented. It uses COX structure, roles, token references, layout notes, and implementation hints to generate TSX placeholders, but it does not invent concrete CSS values, event handlers, or runtime data contracts from prose-only fields.

## Guide and Skill Bundle Intake

The manifest has first-class `GuideDocs` and `SkillBundles` sections.

Current imported content:

- `cox_protocol_package_compiled.zip` was audited as a legacy snapshot of this same package. It was not extracted over the live source because the current repository has the newer COX v1.0 manifest, schema, compiler, package target, and `protocols/` layout. See `guides/imported-packages/cox_protocol_package_compiled.md`.
- `llm_agent_zip_skills_bundle.zip` was expanded into six skill directories under `skills/`.
- NPM installation instructions for another device live in `guides/npm-installation.md`.

Use this intake flow for future ZIP files:

```bash
unzip -l cox_protocol_package_compiled.zip
unzip -l llm_agent_zip_skills_bundle.zip
```

Inspect the listings before extraction. Reject or rename entries with absolute paths, `..` path segments, root-level collisions such as `README.md` or `manifest.cox`, generated caches, or unrelated build artifacts. Curated guide content should land in `guides/`; curated skill bundle content should land in `skills/`. After that, add concrete paths to `GuideDocs` and `SkillBundles`, then rerun validation and compilation.

## Protocol Readiness Score

| Attribute | Meter | Score | Notes |
| --- | --- | ---: | --- |
| Determinism | `[########--]` | 8/10 | Versioned headers, schema-backed manifests, stable package ordering, fixed ZIP timestamps, and SHA-256 records are now in place. Remaining work is an optional generated artifact policy for release bundles. |
| Validation rigor | `[########--]` | 8/10 | YAML parsing, JSON Schema, manifest path checks, target enums, referenced guides, referenced skill bundle directories, and unreferenced `.cox` warnings are active. |
| Evidence traceability | `[########--]` | 8/10 | Evidence and uncertainty protocols are explicit, and the package manifest records exact file hashes. Runtime visual evidence still depends on real screenshots replacing placeholders. |
| Distribution readiness | `[#######---]` | 7/10 | Local Python CLI, NPM wrapper metadata, deterministic package output, VSIX packaging, guide docs, and skill bundle content are present. Public publishing still needs final repository URLs and account tokens. |
| Interoperability | `[#######---]` | 7/10 | COX works as YAML-compatible structured text with JSON, React stub, VS Code, NPM, and ZIP surfaces. A TypeScript-native compiler and concrete design-token CSS layer remain future improvements. |

COX complements Vercel v0 and Stitch-style AI design tools rather than replacing them. Those tools optimize prompt-to-app generation, visual iteration, repo sync, and deployment. COX optimizes deterministic file contracts, evidence tracking, schema validation, reproducible package output, and agent-to-agent handoff.

## Publication and Local Testing

Install and test the Python CLI locally:

```bash
python -m pip install -e .
cox validate .
cox compile . --target json --target react --target package --out build
```

Check the NPM package contents before publishing:

```bash
npm pack --dry-run
npm pack
npm install -g ./cox-protocol-package-<version>.tgz
python3 -m pip install PyYAML jsonschema typer rich
cox-protocol validate .
```

The NPM wrapper delegates to the Python CLI, so the Python dependencies in `requirements.txt` must be installed in the environment used by `cox-protocol`. Set `COX_PYTHON=/path/to/python` if the desired interpreter is not `python3`.

For a device-by-device installation walkthrough, see `guides/npm-installation.md`.

Package the VS Code extension locally:

```bash
cd editor-support/vscode
npm run package
```

Public publishing still requires verified NPM, PyPI, and VS Code Marketplace credentials. Before publishing, confirm the repository URLs in `package.json`, `pyproject.toml`, and `editor-support/vscode/package.json` point to the final public repository.

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
