# COX finalisation acceptance record

Objective: fully finalise the existing COX v1 format and its validator/compiler product, including its distributable tools and an inspectable demonstration. The format remains a structured UI/evidence contract; React output is deliberately structural scaffolding, as specified, rather than an inferred finished application.

## Requirements and proof

- [x] Canonical v1 schemas ship with an installed Python package and npm distribution; ordinary projects do not need a copy of the compiler repository.
- [x] All five document types validate; malformed UTF-8/YAML, duplicate keys, unsupported schemas/versions, broken references and inconsistent page/component bindings produce actionable errors without tracebacks.
- [x] Project-relative paths, source/output separation and generated code identifiers are checked; invalid inputs cannot escape the project/output root or silently overwrite another component.
- [x] JSON and React targets produce deterministic, valid outputs; React scaffolds compile with TypeScript and preserve evidence as explanatory comments.
- [x] Package target includes precisely this run's sources/artifacts with stable ordering/timestamps/permissions and verified SHA-256 records; external output directories work; stale outputs and unrelated files are not incorporated.
- [x] Recompilation safely replaces only tool-owned outputs and never destroys unrelated user files.
- [x] Fresh-project onboarding, human and JSON diagnostics, strict-warning mode and version reporting work through both Python and npm CLIs.
- [x] A small invalid → diagnostic → corrected → compiled fixture demonstrates the real contract, with a reproducible verification command and honest capability boundaries.
- [x] Python wheel/sdist, npm tarball and VS Code extension package cleanly; fresh isolated installs work away from this checkout. Versions, dependency requirements, metadata, schemas and snippets agree.
- [x] Automated regression/integration checks and CI cover the format, compiler, packaging and fresh-install paths. Documentation commands are exercised.
- [x] Release notes, installation guide, format specification, example guide, checksums and a final evidence report are complete. Public release status is explicitly recorded rather than assumed.

## Initial evidence

- Baseline: commit `e5d616c`, matching remote `main`; work continues on `codex/cox-protocol-finalisation`.
- Pre-existing untracked `build/package/` is preserved.
- Baseline `python3 -m tools.cox_cli validate .` passes 17 documents, but reports CLI 1.0.1 while npm metadata says 1.0.2.
- No automated tests or CI are present in the baseline.
- Initial inspection found schema resources are not included in the Python distribution; malformed manifests are indexed before validation errors are handled; package output outside the source root fails; stale generated directories can enter archives; React output accepts unchecked names/content.

Completion requires checking every item above against the final current state. A successful baseline sample or a package build alone is insufficient.

## Release verification — 29 September 2026

- 58 regression/integration tests pass on Python 3.9.6 and Python 3.12.14 using separately installed runtime dependencies. Generated TSX passes TypeScript 7.0.2 with React 19.3.0 types. Node 25.9.0 exercised the wrapper and packaging locally.
- Wheel installed in an isolated Python 3.9 environment; source distribution built and installed in an isolated Python 3.12 environment with an explicit preinstalled build backend. Both pass init, strict validation, invalid binding diagnostics, correction, all-target external compilation and ZIP verification away from the checkout.
- npm tarball installs into a local prefix; its bundled root project validates all 17 documents with zero warnings. The final tarball is checked again through the installed wrapper.
- COX Language Support 1.2.0 artifacts package successfully; all complete-document snippet expansions validate against the canonical schemas. Installation is checked in a separate VS Code data/extension directory.
- The full repository sample compiles to JSON, React and package targets. The generated archive verifies. Tests compare byte-identical builds across two checkout and output locations and exercise modification, collision, stale-file, traversal, symlink, archive-tamper and rollback paths.
- Static Python error/unused-import checks and Git whitespace checks pass. CI covers Python 3.9/3.12/3.14 with Node 22/24, separate wheel/sdist installs and npm/VSIX packaging. CI execution is tracked separately in the pull request; local checks do not establish a remote CI result.
- The baseline's tracked generated build artifacts are removed from version control and ignored. Existing local build files, including the pre-existing untracked package directory, are preserved.

## Distribution status and scope

Release 1.2.0 is prepared as local wheel, sdist, npm tarball and VSIX artifacts with a developer handoff, reproducible demo and checksums. This task has not published to npm, PyPI or the VS Code Marketplace. Registry publication and merging the review branch are separate release actions. Artifact checksums and the final source revision belong in the external handoff record so they cannot create self-referential archive hashes.

The completed scope is the COX v1 design-contract toolchain. React remains typed structural scaffolding. Arbitrary prose rules, rendered UI checks, AST conformance, MCP integration and adoption claims are outside the implemented product. No Windows execution or visual editor interaction is claimed by this local verification. Two upstream Typer/Click deprecation warnings appeared on Python 3.12; all checks passed.

## Pre-merge packaging review — 18 October 2026

- Directory references now reject non-portable descendant filenames before publishing outputs, so compilation cannot emit an archive that its own path verifier rejects.
- ZIP symlink checks now cover every entry, including the embedded inventory rather than only inventoried payload files.
- Six added regression cases cover these paths and bring the suite to 64 tests. The existing CI matrix continues to require generated TypeScript, isolated installs and all four distribution formats for the revised source.
- Registry publication remains a separate action and is outside this review.
