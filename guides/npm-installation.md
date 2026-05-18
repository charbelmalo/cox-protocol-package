# Publishing And Installing COX With NPM

This package ships an NPM command named `cox-protocol`. The command delegates to the Python COX CLI bundled in the package, so target machines need both Node.js and Python.

If the target machine has multiple Python installations, set `COX_PYTHON` to the interpreter that has the COX dependencies installed.

> Note: This NPM package installs the `cox-protocol` command wrapper and the COX package files. The target machine must also have Python 3.10+ and the required Python packages:
>
> ```bash
> python3 -m pip install PyYAML jsonschema typer rich
> ```
>
> Optional when you need to force a specific interpreter:
>
> ```bash
> export COX_PYTHON=/path/to/python
> ```

## Prerequisites

- Node.js 18 or newer
- Python 3.10 or newer
- `pip` available for the Python interpreter you want COX to use
- An npm account with two-factor authentication or an appropriate granular publishing token

## Check `package.json`

Run all publishing commands from the repository root folder that contains `package.json`.

The publish metadata should include:

```json
{
  "name": "cox-protocol-package",
  "version": "1.0.0",
  "description": "NPM wrapper and distribution package for the COX protocol CLI.",
  "license": "MIT",
  "bin": {
    "cox-protocol": "./bin/cox-protocol.js"
  },
  "files": [
    "bin",
    "COX_FILE_FORMAT_SPECIFICATION_v1.0.md",
    "LICENSE",
    "README.md",
    "guides",
    "manifest.cox",
    "protocols",
    "pyproject.toml",
    "requirements.txt",
    "schemas",
    "skills",
    "templates",
    "tools"
  ]
}
```

The `bin` field makes `cox-protocol` available after a global install. The wrapper file must be executable and start with a Node shebang:

```bash
chmod +x bin/cox-protocol.js
head -n 1 bin/cox-protocol.js
```

Expected first line:

```text
#!/usr/bin/env node
```

## Check Package Name Availability

Unscoped npm package names are public and globally unique. Check the current package name:

```bash
npm view cox-protocol-package
```

If npm returns package info, the name is already taken. If it returns a 404, the name can be used.

As of the last local check for this package, both `cox-protocol-package` and `cox-protocol` returned no package version from `npm view`, so either name appeared available. Recheck immediately before publishing because npm names can be claimed at any time.

A shorter public name may be better if it is available:

```bash
npm view cox-protocol
```

If `cox-protocol` is available and you want that name, update `package.json` before publishing:

```json
{
  "name": "cox-protocol"
}
```

Then users install:

```bash
npm install -g cox-protocol
```

## Log In To NPM

Create an npm account, then log in:

```bash
npm login
npm whoami
```

If your account has 2FA enabled, expect an OTP prompt during login or publish. For CI, use a granular npm token with publish permissions.

## Preview The Published Contents

Run a dry run first:

```bash
npm pack --dry-run
```

Then create and inspect the actual tarball:

```bash
npm pack
tar -tzf cox-protocol-package-1.0.0.tgz
```

Confirm the tarball includes:

- `package.json`
- `README.md`
- `bin/cox-protocol.js`
- `tools/` Python CLI files
- `schemas/`, `protocols/`, `templates/`, `guides/`, and `skills/`

Confirm it does not include:

- secrets or `.env` files
- `.venv/`
- `.git/`
- `node_modules/`
- `__pycache__/` or `*.pyc`
- generated tarballs or raw intake ZIPs
- unrelated build or test artifacts

## Test The Tarball Locally

From another temporary folder:

```bash
npm install -g /path/to/cox-protocol-package-1.0.0.tgz
python3 -m pip install PyYAML jsonschema typer rich
cox-protocol --help
```

Then test a real COX project:

```bash
cd /path/to/cox/project
cox-protocol validate .
cox-protocol compile . --target json --target react --target package --out build
```

## Publish To NPM

For an unscoped public package such as `cox-protocol-package`:

```bash
npm publish
```

NPM publishes unscoped packages to the public registry by default. Publishing fails if the same package name and version already exists. Once a version is published, that exact version cannot be reused, even if it is later unpublished.

For a scoped package, such as `@charbel/cox-protocol`, the first public publish must include `--access public`:

```bash
npm publish --access public
```

Scoped packages are not public by default on initial publish.

## Verify Public Installation

After publishing:

```bash
npm view cox-protocol-package
npm install -g cox-protocol-package
cox-protocol --help
```

Then verify a real project:

```bash
python3 -m pip install PyYAML jsonschema typer rich
cd /path/to/cox/project
cox-protocol validate .
cox-protocol compile . --target json --target react --target package --out build
```

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

## Publish Updates Later

Every new publish needs a new version:

```bash
npm version patch
npm publish
```

For larger changes:

```bash
npm version minor
npm publish
```

or:

```bash
npm version major
npm publish
```

## Minimum Manual Publish Sequence

```bash
npm login
npm whoami
npm pack --dry-run
npm pack
npm install -g ./cox-protocol-package-1.0.0.tgz
python3 -m pip install PyYAML jsonschema typer rich
cox-protocol --help
npm publish
npm view cox-protocol-package
```

## Current Limitation

The NPM package is a distribution wrapper, not a TypeScript-native compiler. Python dependencies must be installed separately until the compiler is ported to Node.js or the NPM package gains an installer that manages the Python environment.
