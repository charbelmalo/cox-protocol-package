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

Project entrypoint that defines the package contract, referenced pages, protocol documents, schemas, tooling, and build targets.

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

The first professional compilation target for COX v1.0 is normalized JSON.

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
```

Expected build outputs:

```text
build/
  manifest.compiled.json
  normalized/
  reports/
    verification_report.txt
```

## 9. Editor Support

COX editor support should register `.cox` as its own language id and may initially inherit YAML-compatible tokenization. Header keys such as `CoxVersion`, `FileType`, `Slug`, and `Schema` should be highlighted distinctly.

## 10. Compatibility

COX v1.0 is compatible with YAML tooling that preserves mappings, lists, strings, and nested objects. COX-specific validity is determined by COX schemas rather than YAML parsing alone.