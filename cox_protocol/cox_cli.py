"""Human-readable and machine-readable interfaces to the same COX contract."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from . import __version__
from .cox_lib import CoxError, compile_project, validate_project, fail
from .package_target import verify_archive
from .scaffold import init_project

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Create, validate, compile and verify COX design contracts.",
)
console = Console()


def serializable(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: serializable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serializable(item) for item in value]
    return value


def output(payload, machine: bool, title: str):
    if machine:
        typer.echo(json.dumps(serializable(payload), indent=2))
    else:
        console.print(title, style="bold green", markup=False)
        for key, value in payload.items():
            if key not in ("ok", "target_results"):
                console.print(f"{key}: {serializable(value)}", markup=False)


def failure(exc: Exception, machine: bool):
    if not isinstance(exc, CoxError):
        exc = CoxError(f"I/O operation failed: {exc}")
    if machine:
        typer.echo(json.dumps(exc.as_dict(), indent=2))
    else:
        console.print("COX failed", style="bold red", markup=False)
        console.print(str(exc), markup=False)
    raise typer.Exit(1)


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the tool version.",
    ),
):
    pass


@app.command("validate")
def validate_command(
    project_path: Path = typer.Argument(Path(".")),
    machine: bool = typer.Option(False, "--json", help="Emit JSON diagnostics."),
    strict: bool = typer.Option(False, "--strict", help="Fail on warnings."),
):
    """Check canonical schemas, paths and page/component bindings."""
    try:
        summary = validate_project(project_path)
        if strict and summary.warnings:
            fail("WARNINGS_AS_ERRORS", "\n".join(summary.warnings))
        output(
            {
                "ok": True,
                "version": __version__,
                "project": str(summary.project_root),
                "documentCount": len(summary.documents),
                "warnings": summary.warnings,
            },
            machine,
            "COX validation passed",
        )
    except (CoxError, OSError) as exc:
        failure(exc, machine)


@app.command("compile")
def compile_command(
    project_path: Path = typer.Argument(Path(".")),
    out_dir: Path = typer.Option(Path("build"), "--out", "-o"),
    targets: list[str] = typer.Option(
        [], "--target", "-t", help="json, react, package or all; repeat or use commas."
    ),
    machine: bool = typer.Option(False, "--json"),
    strict: bool = typer.Option(False, "--strict"),
):
    """Compile validated contracts into deterministic JSON, React stubs and ZIPs."""
    try:
        result = compile_project(project_path, out_dir, targets=targets, strict=strict)
        output({"ok": True, **result}, machine, "COX compilation passed")
    except (CoxError, OSError) as exc:
        failure(exc, machine)


@app.command("init")
def init_command(
    destination: Path = typer.Argument(...),
    name: Optional[str] = typer.Option(None, "--name"),
    machine: bool = typer.Option(False, "--json"),
):
    """Create a complete example project in a new or empty directory."""
    try:
        output(
            {"ok": True, "project": init_project(destination, name)},
            machine,
            "COX project created",
        )
    except (CoxError, OSError) as exc:
        failure(exc, machine)


@app.command("verify-package")
def verify_command(
    archive: Path = typer.Argument(...), machine: bool = typer.Option(False, "--json")
):
    """Verify ZIP contents against the embedded SHA-256 inventory (not a signature)."""
    try:
        output(verify_archive(archive), machine, "COX package verified")
    except (CoxError, OSError) as exc:
        failure(exc, machine)


if __name__ == "__main__":
    app()
