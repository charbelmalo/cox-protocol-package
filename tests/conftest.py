import shutil
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    folder = tmp_path / "source"
    shutil.copytree(ROOT / "examples" / "quickstart", folder)
    return folder


def change(project, rel, mutate):
    path = project / rel
    doc = yaml.safe_load(path.read_text())
    mutate(doc)
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    return doc
