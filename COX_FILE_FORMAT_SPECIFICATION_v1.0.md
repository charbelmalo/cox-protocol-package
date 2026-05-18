# COX File Format Specification v1.0

## 1. Status

- Format name: `COX`
- Version: `1.0`
- File extension: `.cox`
- MIME type: `application/vnd.cox+yaml`
- Encoding: `UTF-8`
- Syntax base: `YAML-compatible structured text`
- Entry point: `manifest.cox`

## 2. Purpose

COX is a structured file format for UI reconstruction, evidence tracking, component binding, implementation guidance, and agent-readable design specifications. A COX project is manifest-driven and intended to be both human-readable and machine-validatable.

## 3. Common Header

Every `.cox` document must begin with the following versioned metadata header:

```yaml
CoxVersion: "1.0"
FileType: "component_spec"
Slug: "projects_grid_cards"
Schema: "cox.component.v1"
```

Required header fields for all COX documents:

- `CoxVersion`
- `FileType`
- `Slug`
- `Schema`

## 4. Supported File Types

### `manifest`

Project entrypoint that defines the package contract, referenced pages, guide documents, protocol documents, skill bundles, schemas, tooling, and build targets.

Required top-level fields:

- `CoxVersion`
- `FileType`
- `Slug`
- `Schema`
- `ProjectName`
- `ProtocolExtension`
- `MimeType`
- `EntryPoint`
- `Pages`

Optional manifest file collections:

- `ReferenceDocs`: human-facing root documentation files
- `GuideDocs`: guide or tutorial files imported into `guides/`
- `ProtocolDocs`: `.cox` methodology and system protocol documents
- `SkillBundles`: LLM-agent skill bundle files or directories imported into `skills/`
- `Schemas`: JSON Schema files used by the validator
- `ToolingFiles`: compiler, editor, package, and distribution tooling files

Supported build targets:

- `json`
- `react`
- `package`

### `page_spec`

Defines page-level evidence, visible regions, child component bindings, layout behavior, and page interactions.

Required top-level fields:

- `CoxVersion`
- `FileType`
- `PageName`
- `Slug`
- `Schema`
- `ProjectName`
- `EvidenceSummary`
- `VisibleStructure`
- `Interactions`

### `component_spec`

Defines a reusable UI component, its evidence basis, visible structure, visual style, and interactions.

Required top-level fields:

- `CoxVersion`
- `FileType`
- `ComponentName`
- `Slug`
- `Schema`
- `EvidenceSummary`
- `VisibleStructure`
- `Interactions`

### `protocol_doc`

Defines COX process rules, naming conventions, orchestration rules, logic notes, design tokens, or validation checklists.

Required top-level fields:

- `CoxVersion`
- `FileType`
- `Slug`
- `Schema`
- `ProtocolName`
- `Purpose`

### `crop_metadata`

Defines crop planning metadata for derived screenshots.

Required top-level fields:

- `CoxVersion`
- `FileType`
- `Slug`
- `Schema`
- `SourceScreenshot`
- `OutputScreenshot`
- `BoundaryConfidence`
- `EstimatedBoundingBox`

## 5. Slug Rules

`Slug` values use lowercase snake case.

Allowed pattern:

```text
^[a-z0-9]+(_[a-z0-9]+)*$
```

Examples:

- `dashboard`
- `projects_grid_cards`
- `deterministic_naming_convention`

## 6. Evidence Model

When evidence is relevant, COX documents should separate claims into explicit evidence levels:

- `Visible`
- `UserSpecified`
- `Inferred`
- `Intended`
- `Recommended`

The format does not permit inferred behavior to be represented as certain without explicit visible or user-provided evidence.

## 7. Validation Model

COX documents are parsed as YAML and validated against JSON Schema Draft 2020-12.

Canonical schema ids:

- `cox.manifest.v1`
- `cox.page.v1`
- `cox.component.v1`
- `cox.protocol.v1`
- `cox.crop_metadata.v1`

Validation must include:

- UTF-8 decoding
- YAML parsing
- Schema validation
- Manifest reference existence checks
- Page/component path checks
- Unreferenced `.cox` file detection as a warning

## 8. Compilation Model

The first professional compilation target for COX v1.0 is normalized JSON. The current compiler also supports React stubs and deterministic package ZIP output.

Expected pipeline:

```text
.cox files
  -> parse YAML
  -> validate against schema
  -> check references and paths
  -> emit normalized JSON
  -> generate verification report
```

Recommended commands:

```bash
cox validate ./cox_protocol_package
cox compile ./cox_protocol_package --out ./build
cox compile ./cox_protocol_package --target react --out ./build
cox compile ./cox_protocol_package --target json --target react --target package --out ./build
```

Expected build outputs:

```text
build/
  manifest.compiled.json
  normalized/
  package/
    cox_protocol_package_corrected.zip
    cox_protocol_package_corrected.manifest.json
  reports/
    verification_report.txt
```

Optional React stub output:

```text
build/
  react/
    components/
    pages/
    index.ts
    manifest.react.json
```

The `react` target consumes the same normalized COX document model used by the JSON target and emits framework-neutral TSX stubs. COX v1.0 does not require the compiler to infer concrete CSS values or executable interaction logic from prose-only layout and evidence sections.

The `package` target emits a deterministic ZIP archive from manifest-referenced source files and any generated outputs produced earlier in the same compilation pass. Package archives must use project-relative paths under a single archive root, sorted file ordering, fixed ZIP timestamps, and SHA-256 records for every packaged file. Local caches, virtual environments, raw intake ZIPs, and package output directories must not be included.

Guide and skill bundle intake is intentionally explicit. The compiler supports `GuideDocs` and `SkillBundles`, but ZIP attachments must be inspected and curated before their paths are added to the manifest.

## 9. Editor Support

COX editor support should register `.cox` as its own language id and may initially inherit YAML-compatible tokenization. Header keys such as `CoxVersion`, `FileType`, `Slug`, and `Schema` should be highlighted distinctly.

## 10. Compatibility

COX v1.0 is compatible with YAML tooling that preserves mappings, lists, strings, and nested objects. COX-specific validity is determined by COX schemas rather than YAML parsing alone.