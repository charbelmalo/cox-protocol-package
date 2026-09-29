#!/usr/bin/env python3
"""Record a real COX binding failure, correction and deterministic build."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from cox_protocol.cox_lib import CoxError, compile_project, validate_project, write_json
from cox_protocol.package_target import verify_archive
from cox_protocol.scaffold import init_project


def demo(out: Path):
    out = out.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("Use a new or empty demo output directory.")
    out.mkdir(parents=True, exist_ok=True)
    project = init_project(out / "project", "Contract Demo")
    component = project / "page/action_button/action_button.cox"
    corrected = component.read_text()
    invalid = corrected.replace("Slug: action_button", "Slug: action_buton")
    component.write_text(invalid)
    try:
        validate_project(project)
    except CoxError as exc:
        diagnostic = exc.as_dict()
    else:
        raise RuntimeError("Expected the broken binding to fail")
    finally:
        component.write_text(corrected)
    (out / "01-invalid-component.cox.txt").write_text(invalid)
    write_json(out / "02-diagnostic.json", diagnostic)
    (out / "03-corrected-component.cox.txt").write_text(corrected)
    summary = validate_project(project)
    build = compile_project(project, out / "build", ["all"], strict=True)
    verified = verify_archive(build["target_results"]["package"]["archive"])
    verified["archive"] = Path(verified["archive"]).relative_to(out).as_posix()
    evidence = {
        "ok": True,
        "rule": "Each component Slug must match its manifest binding.",
        "observedDiagnostic": diagnostic,
        "correction": "action_buton → action_button",
        "validatedDocuments": len(summary.documents),
        "archive": verified,
        "scope": "Contract validation and structural React scaffolding; no rendered UI or AST compliance evaluation.",
    }
    write_json(out / "04-result.json", evidence)
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(out),
                "validatedDocuments": len(summary.documents),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    demo(parser.parse_args().out)
