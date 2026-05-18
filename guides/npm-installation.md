# Installing COX On Another Device With NPM

This package ships an NPM command named `cox-protocol`. The command delegates to the Python COX CLI bundled in the package, so the target device needs both Node.js and Python.

## Prerequisites

- Node.js 18 or newer
- Python 3.10 or newer
- `pip` available for the Python interpreter you want COX to use

## Install From NPM After Publication

```bash
npm install -g cox-protocol-package
python3 -m pip install PyYAML jsonschema typer rich
```

Then validate a COX project:

```bash
cd /path/to/cox/project
cox-protocol validate .
cox-protocol compile . --target json --target react --target package --out build
```

## Install From A Local NPM Tarball

On the development machine, create the tarball:

```bash
npm pack
```

Copy `cox-protocol-package-1.0.0.tgz` to the other device, then install it there:

```bash
npm install -g ./cox-protocol-package-1.0.0.tgz
python3 -m pip install PyYAML jsonschema typer rich
```

Run the same smoke test from any COX project folder:

```bash
cox-protocol validate .
cox-protocol compile . --target json --target react --target package --out build
```

## Use A Specific Python Interpreter

If the device has multiple Python installations, set `COX_PYTHON`:

```bash
COX_PYTHON=/path/to/python3 cox-protocol validate .
```

For a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install PyYAML jsonschema typer rich
COX_PYTHON="$PWD/.venv/bin/python" cox-protocol validate .
```

## Confirm The Install

```bash
cox-protocol --help
cox-protocol validate /path/to/cox/project
```

A successful install prints `COX validation passed` and reports the validated document count.

## Current Limitation

The NPM package is a distribution wrapper, not a TypeScript-native compiler. Python dependencies must be installed separately until the compiler is ported to Node.js or the NPM package gains an installer that manages the Python environment.
