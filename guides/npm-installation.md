# Installing the npm wrapper

The npm package ships the same Python compiler and schema resources. It requires Node 18+, Python 3.9+, and the Python dependencies in the interpreter selected by `COX_PYTHON`. It never installs Python packages automatically.

For the local 1.2.0 release artifacts on macOS/Linux:

```bash
python3 -m venv .cox-venv
.cox-venv/bin/python -m pip install /path/to/cox_protocol_package-1.2.0-py3-none-any.whl
export COX_PYTHON="$PWD/.cox-venv/bin/python"
npm install --prefix ./cox-tools /path/to/cox-protocol-package-1.2.0.tgz
./cox-tools/node_modules/.bin/cox-protocol --version
./cox-tools/node_modules/.bin/cox-protocol init my-contract --name MyProject
./cox-tools/node_modules/.bin/cox-protocol validate my-contract --strict
./cox-tools/node_modules/.bin/cox-protocol compile my-contract --target all --out build
./cox-tools/node_modules/.bin/cox-protocol verify-package my-contract/build/package/myproject.zip
```

The local npm prefix avoids changing global packages. On Windows, use the virtual environment's `Scripts/python.exe`, set `$env:COX_PYTHON`, and invoke the `.cmd` launcher from PowerShell. Windows execution is not covered by the local macOS release check.

If using the npm tarball without a wheel, install its `requirements.txt` into that virtual environment using `python -m pip install -r cox-tools/node_modules/cox-protocol-package/requirements.txt`. Runtime source and canonical schemas are bundled in the npm package.

`cox-protocol --version` works without Python. Other commands explain a missing interpreter or dependencies. The wrapper removes the caller's current directory and PYTHONPATH from module resolution before loading the bundled CLI to avoid accidental module shadowing.

Use a version available in the selected registry when installing by package name. Building a local 1.2.0 artifact does not publish it; see the release record for status.
