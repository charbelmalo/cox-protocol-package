# Changelog

## 1.2.0 — 2026-09-29

- Ship canonical schemas and a complete starter inside the namespaced Python package; align Python, npm and VS Code versions.
- Add `init`, `--json`, `--strict`, `--version` and `verify-package` CLI surfaces.
- Reject ambiguous YAML, invalid project paths and inconsistent manifest/page/component bindings with structured diagnostics.
- Support shared component folders within the project; prevent generated identifier and output-path collisions.
- Preserve evidence in safely escaped React comments and validate generated scaffolds with TypeScript.
- Stage builds before publication, track generated-file ownership, preserve unrelated files, refuse local-edit overwrites and remove only stale owned output.
- Support external output directories and deterministic archives containing the current run's compiled manifest and reports; verify inventory hashes, sizes, paths and modes.
- Reject non-portable filenames inside referenced source directories before packaging, and reject symlink metadata on every ZIP entry, including the inventory.
- Add regression tests, clean-install release checks, CI and a reproducible failing/corrected contract demonstration.
- Replace subjective readiness scores with explicit capability boundaries and verification evidence.

### Migration

COX format remains 1.0. Duplicate YAML keys, aliases, non-JSON YAML values, unknown evidence labels, unsafe paths and mismatched bindings now fail validation. Quote textual YAML boolean words and dates. Use a new output folder for old builds without an ownership marker. The installed Python module is `cox_protocol`; source-checkout `tools` entry points remain compatibility shims. React output remains structural scaffolding.

## Earlier releases

The baseline used Python 1.0.1, npm 1.0.2, and VS Code extension 1.1.0. It provided schema validation, JSON/React/package targets and syntax/snippet support. Historical intake notes remain under `guides/imported-packages/`.
