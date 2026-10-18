"""Create a self-contained COX project from the installed starter assets."""

from __future__ import annotations
from pathlib import Path
import os
import re
import shutil
import tempfile
import yaml
from .cox_lib import CoxError, fail, portable_segment, validate_project


def init_project(destination: Path, name: str | None = None) -> Path:
    if destination.is_symlink():
        fail("INIT_EXISTS", "Destination must not be a symlink", str(destination))
    destination = destination.resolve()
    if destination.exists() and (
        not destination.is_dir() or any(destination.iterdir())
    ):
        fail(
            "INIT_EXISTS",
            "Destination must be new or empty; existing files are preserved",
            str(destination),
        )
    title = name or destination.name
    if not portable_segment(title):
        fail(
            "PROJECT_NAME",
            "Choose a non-empty portable project name, without path separators",
            title,
        )
    slug = re.sub("[^a-z0-9]+", "_", title.lower()).strip("_") or "cox_project"
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".cox-init-", dir=destination.parent
        ) as temp:
            stage = Path(temp) / "project"
            shutil.copytree(Path(__file__).parent / "starter", stage)
            for rel in ["manifest.cox", "page/page.cox"]:
                path = stage / rel
                doc = yaml.safe_load(path.read_text(encoding="utf-8"))
                doc["ProjectName"] = title
                if rel == "manifest.cox":
                    doc["Slug"] = slug
                    doc["PackageName"] = slug + ".zip"
                path.write_text(
                    yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
            validate_project(stage)
            # rename refuses a concurrently populated destination directory.
            os.replace(stage, destination)
        return destination
    except OSError as exc:
        raise CoxError(f"Could not create project: {exc}") from exc
