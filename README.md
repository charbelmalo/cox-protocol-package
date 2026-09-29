# COX Protocol

**A design contract you can inspect, validate, and hand off.** COX records UI structure and the evidence behind a design decision in versioned `.cox` files. Its CLI checks the contract and generates normalized JSON, structural React scaffolds, and a reproducible ZIP with a SHA-256 inventory.

Tool release **1.2.0** implements format **1.0**. Python 3.9+ is required; the optional npm wrapper also requires Node 18+.

## Try it

Install the release wheel in an isolated environment (replace the wheel path with your downloaded artifact):

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install /path/to/cox_protocol_package-1.2.0-py3-none-any.whl
cox --version
cox init my-contract --name MyProject
cox validate my-contract --strict
cox compile my-contract --target all --out build
cox verify-package my-contract/build/package/myproject.zip
```

Relative `--out` paths are resolved **inside the COX project**. Absolute output directories also work. `python -m cox_protocol` provides the same commands as `cox`.

For a source checkout, replace the wheel installation with `python -m pip install -e '.[dev]'`. The npm installation guide is [here](guides/npm-installation.md). These commands refer to local release artifacts; consult [the release record](FINALIZATION.md) for publication status before assuming 1.2.0 is available on a registry.

## One rule, an observable failure, a correction

A manifest binds a component to `action_button`. Change the component document's `Slug` to `action_buton` and validation reports `BINDING_MISMATCH`, the file, the `Slug` field, and both values. Restore the slug and all targets compile.

Run the complete walkthrough from a source checkout after installing the package:

```bash
python scripts/demo.py --out /tmp/cox-contract-demo
```

It saves the invalid input, actual diagnostic, corrected input, verification result, generated React, and package. Use a new output folder on each run. [Example guide](guides/contract-demo.md).

## What is checked

- UTF-8 and a JSON-compatible YAML subset, with duplicate keys, aliases, non-string keys, dates and non-finite numbers rejected.
- Five canonical Draft 2020-12 schemas, shipped with the compiler: manifest, page, component, protocol, crop metadata.
- Manifest references, file/directory expectations, project boundaries, and page/component identity and folder bindings.
- Evidence labels: `Visible`, `UserSpecified`, `Inferred`, `Intended`, `Recommended`. Their factual accuracy still requires human evidence review.
- Generated identifiers, collisions, output ownership and archive inventory integrity.

The contract describes an interface. It does **not** inspect an application's AST, execute design rules against a rendered page, implement interactions, prove accessibility, or provide an MCP server. The React target emits typed structural scaffolds with evidence comments; it does not infer finished styling or behavior. Protocol prose and `VerificationRules` are authoring guidance, not arbitrary executable rules.

## Commands

| Command | Result |
|---|---|
| `cox init PATH --name NAME` | Complete small project; destination must be new or empty |
| `cox validate PATH --json` | Machine-readable diagnostics with exit 1 on invalid input |
| `cox validate PATH --strict` | Also fail on unreferenced-document warnings |
| `cox compile PATH --target json` | Normalized JSON (the default target) |
| `cox compile PATH -t react -t package` | Requested targets in stable order |
| `cox compile PATH -t all --json` | All three targets and artifact paths as JSON |
| `cox verify-package FILE.zip --json` | Check every payload against its embedded size/hash/mode record |
| `cox --version` | Tool version |

`--target` accepts repeated flags and comma-separated values. `BuildTargets` records supported project intent; the command selects which targets to emit and defaults to JSON. Usage errors exit 2; validation, compilation and verification failures exit 1. JSON mode applies to command results; argument parsing errors retain the CLI's normal usage format.

## Build artifacts and ownership

```text
build/
  .cox-build.json                 # exact files owned by this compiler run
  manifest.compiled.json
  normalized/                    # selected json target
  react/                         # selected react target
  package/                       # selected package target
  reports/verification_report.json
  reports/verification_report.txt
```

The package includes manifest-referenced inputs and artifacts generated in the current run, under the manifest slug. Entries have sorted names, fixed timestamps, normalized permissions, and SHA-256 records. The external inventory also records the ZIP's checksum. Neither inventory is a digital signature. Determinism is verified for identical input bytes/modes and toolchain; ZIP compression bytes may differ between compression-library versions.

Recompilation replaces only the exact generated files recorded in `.cox-build.json`. Files from deselected targets are removed; unrelated files are preserved. A collision, edited generated file, or symlink produces an error before publication. Use a fresh `--out` directory for legacy builds without an ownership marker or when preserving edits. There is no force-overwrite mode. Publication attempts rollback on I/O failure; it is not a concurrent-writer or power-loss transaction.

## Development and release checks

Use Node 22+ for development packaging; Node 18+ remains sufficient for the runtime wrapper.

```bash
python -m pip install -e '.[dev]'
npm ci
COX_REQUIRE_TYPESCRIPT=1 python -m pytest
python scripts/release_check.py
python -m build
npm pack
npm run package:vscode
```

The tests exercise format errors, bindings, generated TypeScript, deterministic archives, tamper detection, safe rebuilds, CLI behavior and snippet validity. CI additionally installs a wheel and an sdist into separate environments, installs the npm tarball locally, and verifies their CLIs away from the checkout. Python schemas and starter files must work from the installed package alone.

## Contents

- `cox_protocol/`: installed compiler, canonical schema resources, starter assets.
- `schemas/`: matching public schemas for external tooling.
- `examples/quickstart/`: independent, small project with reference illustrations.
- `LocalAppManager/` and root `manifest.cox`: larger sample with explicitly labelled screenshot placeholders.
- `protocols/`, `templates/`, `skills/`, `guides/`: human/agent authoring material.
- `editor-support/vscode/`: syntax highlighting and snippets; CLI validation is separate.
- `tools/`: compatibility entry points for older source-checkout commands.

The [format specification](COX_FILE_FORMAT_SPECIFICATION_v1.0.md), [changelog](CHANGELOG.md), and [finalisation record](FINALIZATION.md) describe the implemented contract and release evidence. The [historical intake guide](guides/imported-packages/cox_protocol_package_compiled.md) records earlier archive provenance.
