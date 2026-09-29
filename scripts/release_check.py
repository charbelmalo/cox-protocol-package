#!/usr/bin/env python3
"""Exercise an installed CLI away from its checkout; no repository imports."""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def check(command, env=None):
    with tempfile.TemporaryDirectory(prefix="cox-installed-") as raw:
        root = Path(raw)

        def run(*args, expected=0):
            result = subprocess.run(
                [*command, *args], cwd=root, env=env, capture_output=True, text=True
            )
            if result.returncode != expected:
                raise RuntimeError(
                    f"{args}: exit {result.returncode}\n{result.stdout}\n{result.stderr}"
                )
            return result.stdout

        version = run("--version").strip()
        assert json.loads(run("init", "demo", "--json"))["ok"]
        assert (
            json.loads(run("validate", "demo", "--json", "--strict"))["documentCount"]
            == 3
        )
        component = root / "demo/page/action_button/action_button.cox"
        original = component.read_text()
        component.write_text(
            original.replace("Slug: action_button", "Slug: action_buton")
        )
        invalid = json.loads(run("validate", "demo", "--json", expected=1))
        assert invalid["errors"][0]["code"] == "BINDING_MISMATCH"
        component.write_text(original)
        result = json.loads(
            run(
                "compile",
                "demo",
                "--target",
                "all",
                "--out",
                str(root / "artifacts"),
                "--json",
                "--strict",
            )
        )
        archive = Path(result["target_results"]["package"]["archive"])
        assert json.loads(run("verify-package", str(archive), "--json"))["ok"]
        print(
            json.dumps(
                {
                    "ok": True,
                    "version": version,
                    "command": command,
                    "checks": [
                        "init",
                        "strict validation",
                        "invalid binding diagnostic",
                        "corrected all-target compile",
                        "external output",
                        "archive verification",
                    ],
                }
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--node-cli", type=Path)
    args = parser.parse_args()
    if args.node_cli:
        check(
            ["node", str(args.node_cli.resolve())],
            {**os.environ, "COX_PYTHON": args.python},
        )
    else:
        check([args.python, "-m", "cox_protocol"])
