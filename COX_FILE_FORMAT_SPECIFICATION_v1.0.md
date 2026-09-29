# COX file format 1.0

This specification accompanies compiler 1.2.0. The executable field contract is defined by the five JSON Schemas in `schemas/`, mirrored in the installed `cox_protocol/schemas/` package.

## Representation

COX uses `.cox`, UTF-8, and the descriptive MIME type `application/vnd.cox+yaml`. Each project has one `manifest.cox` entry point. Documents are YAML mappings with JSON-compatible values: string keys; mappings; arrays; strings; booleans; finite numbers; null. Key order is not significant. Common headers should appear first for readability, but the parser does not require an order.

The implementation uses PyYAML's safe scalar resolution. Quote version strings, dates, and textual YAML boolean words such as `Yes`, `No`, `on`, and `off`. Duplicate keys, aliases (including merge aliases), non-string keys, YAML-specific object types, timestamps and non-finite numbers are rejected. Unsupported custom tags are rejected. Anchors without references add no semantics. One document per file is supported.

```yaml
CoxVersion: "1.0"
FileType: "component_spec"
Slug: "action_button"
Schema: "cox.component.v1"
```

All documents require these four fields. `CoxVersion` must be the string `1.0`. Slugs match `^[a-z0-9]+(_[a-z0-9]+)*$`. A document's `FileType` and `Schema` must correspond exactly.

## Document types

The following required fields are **in addition to the four common fields**. See the schemas for nested requirements, enums and optional fields.

| FileType | Schema | Additional required fields |
|---|---|---|
| manifest | cox.manifest.v1 | ProjectName, ProtocolExtension, MimeType, EntryPoint, Pages |
| page_spec | cox.page.v1 | PageName, ProjectName, EvidenceSummary, VisibleStructure, Interactions, NamingDecision, Layout, Children, RecursiveDecompositionDecision |
| component_spec | cox.component.v1 | ComponentName, Role, EvidenceSummary, VisibleStructure, Interactions, NamingDecision |
| protocol_doc | cox.protocol.v1 | ProtocolName, Purpose |
| crop_metadata | cox.crop_metadata.v1 | SourceScreenshot, OutputScreenshot, BoundaryConfidence, EstimatedBoundingBox |

A manifest requires at least one page. `ProtocolExtension`, `MimeType`, and `EntryPoint` use the fixed values `.cox`, `application/vnd.cox+yaml`, and `manifest.cox`. Every page entry includes `PageName`, `Slug`, `Folder`, `PageInstruction`, `PageScreenshotPlaceholder`, and `Components`. Component entries include `Slug`, `Folder`, `ComponentInstruction`, and `ComponentScreenshotPlaceholder`. Empty component arrays are permitted.

`NamingDecision` records ChosenName, Reason, RejectedAlternatives, AmbiguityRisk, and EvidenceLevel. Layout requires Desktop, Tablet, and Mobile strings. COX v1 permits extensible prose fields in several objects; passing schema validation does not make those fields executable.

## Evidence

`EvidenceSummary` and `Interactions` accept the five evidence labels `Visible`, `UserSpecified`, `Inferred`, `Intended`, and `Recommended`, each an array of strings. Unknown labels are rejected. A naming decision's EvidenceLevel must use the same vocabulary. These categories distinguish observation, supplied requirements, interpretation, desired behavior, and suggestions.

The tool checks the representation and vocabulary, not whether an observation is true. Screenshot placeholders and generated reference illustrations must be described honestly. Crop metadata is a planning document: screenshot strings and bounding-box descriptions are not a pixel-analysis or file-existence guarantee.

## References and bindings

Manifest paths are relative POSIX paths within the project. Absolute paths, backslashes, parent traversal and symlink references are rejected. Referenced inputs must exist. Page/component instructions and their screenshot/placeholder files must be regular files inside the corresponding Folder. Instruction files use `.cox`.

The page document's Slug, PageName and ProjectName must match its manifest entry and project. Page slugs are unique. A component document's Slug must match its manifest binding. A shared component slug may be reused when it names the same source; different source files may not claim the same component slug.

`Children.Components` must match that page's manifest component set, without duplicates. Each child's Folder is relative to the page instruction's directory. It may use `..` to reach a shared component **within** the project; it cannot escape the project or traverse symlinks.

Optional input collections are ReferenceDocs, GuideDocs, ProtocolDocs, SkillBundles, Schemas and ToolingFiles. ProtocolDocs must contain protocol document files. Referenced `.cox` files under GuideDocs and SkillBundles are also validated. Other collections include assets/documentation without interpreting arbitrary files as COX. The compiler always uses its installed canonical schemas; the Schemas collection packages supporting files and cannot override validation rules.

Unreferenced `.cox` files produce a warning; `--strict` makes that warning an error. Nested independent projects, managed build outputs and transient directories are excluded from this scan. `VerificationRules` and protocol text are guidance, not dynamically executed code.

## Compilation

Validation precedes every build. CLI targets are `json`, `react`, `package`, and `all`. Repeated/comma-separated target arguments are normalized into stable order. Without a target the compiler emits JSON. Manifest BuildTargets is descriptive project metadata.

- **JSON:** normalized documents preserving data and evidence; compiled manifest records relative input/output paths.
- **React:** typed TSX page/component scaffolds with source evidence comments. Snake-case slugs become PascalCase; numeric starts receive `Cox`. Conflicting generated symbols are errors. ProjectName must be a portable single directory name. Prose is safely escaped. No finished CSS, event behavior, data fetching, AST conformance or rendered compliance is inferred.
- **Package:** a single-root ZIP named by PackageName or Slug. The root is the manifest slug, independent of checkout location. It contains declared sources and only artifacts from this invocation, including the compiled manifest and verification report.

Relative output paths are relative to the discovered project. Absolute external outputs are supported. Output parents are canonicalized, including standard OS temporary-directory aliases. The output directory itself and managed paths within it may not be symlinks. Canonical output paths may not overlap source inputs, the project root or an ancestor. Builds stage independently and publish only owned files; `.cox-build.json` records their exact hashes. Unknown collisions and human-modified artifacts are preserved with a diagnostic. A target removed from the command removes only its prior owned files.

## Archive contract

Names are sorted, timestamps fixed at 1980-01-01, permissions normalized to 0644 (or 0755 for executable source files), and archive paths use POSIX separators. Cache/build directories, Python bytecode, environment files and identified historical raw intake archives are excluded. Explicit references to excluded inputs fail packaging.

The embedded `package.manifest.json` inventories payload entries with path, source, kind, size, SHA-256 and mode. It excludes itself to avoid a self-referential hash. `fileCount` counts those payload entries; the ZIP has one additional inventory entry. An external `.manifest.json` additionally records the complete ZIP's size and SHA-256. The ZIP does not contain itself or this external inventory.

`cox verify-package` checks entry uniqueness, portable paths, a single root inventory, exact inventory coverage, sizes, hashes, permissions and absence of symlink entries. It does not establish author identity or protect against an attacker replacing both files and the inventory. Verify a trusted external checksum when provenance matters. Byte-for-byte reproducibility is scoped to identical input bytes/modes and compression toolchain.

## Errors and compatibility

Commands support `--json`, returning `ok` and either result fields or `errors` with code, message, path and location. Invalid contracts/builds/archives exit 1. CLI usage errors exit 2 with the normal argument-parser message. `--strict` is supported for validation and compilation.

Tool versions and file-format versions are independent. Compiler 1.2.0 strengthens diagnostics and rejects previously ambiguous input (duplicate keys, aliases, schema-label typos, inconsistent bindings and unsafe paths). Existing valid format-1.0 projects remain supported. Legacy generated folders without `.cox-build.json` should be rebuilt into a fresh directory. The npm wrapper invokes Python; it is not an independent TypeScript implementation. The VS Code extension provides syntax and snippets, with validation through the CLI.
