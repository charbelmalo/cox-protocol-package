import json
import os
import re
import shutil
import subprocess
import sys
import pytest
from typer.testing import CliRunner
from cox_protocol import __version__
from cox_protocol.cox_cli import app
from cox_protocol.cox_lib import compile_project, schema_issues
from conftest import ROOT, change


def test_version_and_snippets():
    assert CliRunner().invoke(app, ["--version"]).output.strip() == __version__
    assert json.loads((ROOT / "package.json").read_text())["version"] == __version__
    assert (
        json.loads((ROOT / "editor-support/vscode/package.json").read_text())["version"]
        == __version__
    )
    assert f'version = "{__version__}"' in (ROOT / "pyproject.toml").read_text()
    import yaml

    for path in (ROOT / "editor-support/vscode/snippets").glob("cox-*.json"):
        if path.name == "cox-common.json":
            continue
        for snippet in json.loads(path.read_text()).values():
            body = "\n".join(snippet["body"])
            body = re.sub(r"\$\{\d+:([^}]+)\}", r"\1", body)
            body = re.sub(r"\$\{\d+\|([^,|]+)[^}]*\|\}", r"\1", body)
            assert not schema_issues(yaml.safe_load(body), path), path


def test_node_wrapper_cwd_isolation_and_errors(project, tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node integration runs in the release/CI environment")
    for name in ("yaml.py", "cox_protocol.py", "jsonschema.py"):
        (project / name).write_text(
            'raise RuntimeError("Caller module must not be imported")'
        )
    env = {**os.environ, "COX_PYTHON": sys.executable}
    wrapper = ROOT / "bin/cox-protocol.js"
    version = subprocess.run(
        [node, str(wrapper), "--version"],
        capture_output=True,
        text=True,
        env=env,
        cwd=project,
    )
    assert version.returncode == 0 and version.stdout.strip() == __version__
    result = subprocess.run(
        [node, str(wrapper), "validate", ".", "--json"],
        capture_output=True,
        text=True,
        env=env,
        cwd=project,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["ok"] is True
    change(project, "manifest.cox", lambda d: d.update(CoxVersion="unknown"))
    bad = subprocess.run(
        [node, str(wrapper), "validate", ".", "--json"],
        capture_output=True,
        text=True,
        env=env,
        cwd=project,
    )
    assert bad.returncode == 1
    assert json.loads(bad.stdout)["errors"]
    missing = subprocess.run(
        [node, str(wrapper), "--help"],
        capture_output=True,
        text=True,
        env={**env, "COX_PYTHON": str(tmp_path / "absent")},
    )
    assert missing.returncode == 1 and "COX needs Python" in missing.stderr


def test_generated_tsx_typechecks(project, tmp_path):
    tsc = ROOT / "node_modules/typescript/bin/tsc"
    if not tsc.exists():
        if os.environ.get("COX_REQUIRE_TYPESCRIPT") == "1":
            pytest.fail("npm ci is required before this gate")
        pytest.skip("Run npm ci to enable the TypeScript release gate")
    change(
        project,
        "page/action_button/action_button.cox",
        lambda d: d.update(
            Role='Quoted "role" </section> */\nnext line',
            ImplementationHints=["*/\nexport const wrong = 1"],
        ),
    )
    out = tmp_path / "consumer"
    compile_project(project, out, ["react"])
    (out / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
    (out / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "strict": True,
                    "noEmit": True,
                    "jsx": "react-jsx",
                    "target": "ES2020",
                    "module": "ESNext",
                    "moduleResolution": "Bundler",
                    "skipLibCheck": True,
                },
                "include": ["react/**/*.ts", "react/**/*.tsx"],
            }
        )
    )
    checked = subprocess.run(
        ["node", str(tsc), "--project", str(out / "tsconfig.json")],
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert (
        "EvidenceSummary.Intended:"
        in (out / "react/components/ActionButton/index.tsx").read_text()
    )
