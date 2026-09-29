import json
import shutil
from pathlib import Path
import pytest
from typer.testing import CliRunner
from cox_protocol.cox_cli import app
from cox_protocol.cox_lib import (
    CoxError,
    read_yaml_document,
    schema_issues,
    validate_project,
)
from cox_protocol.scaffold import init_project
from conftest import ROOT, change

runner = CliRunner()


def code(exc):
    return exc.value.issues[0].code


def test_self_contained_starter_and_repository(project):
    assert not (project / "schemas").exists()
    assert len(validate_project(project).documents) == 3
    assert len(validate_project(ROOT).documents) >= 17
    for source in (ROOT / "schemas").glob("*.json"):
        assert (
            source.read_bytes()
            == (ROOT / "cox_protocol/schemas" / source.name).read_bytes()
        )


@pytest.mark.parametrize(
    "body,expected",
    [
        ("[broken", "YAML_INVALID"),
        ("[]", "DOCUMENT_TYPE"),
        ("hello: one\nhello: two", "YAML_INVALID"),
        ("hello: &a [*a]", "YAML_INVALID"),
        ("hello: 2026-01-01", "YAML_INVALID"),
        ("hello: .nan", "YAML_INVALID"),
        ("true: value", "YAML_INVALID"),
        ("hello: !!python/object:object {}", "YAML_INVALID"),
    ],
)
def test_invalid_documents_never_traceback(tmp_path, body, expected):
    p = tmp_path / "bad.cox"
    p.write_text(body)
    with pytest.raises(CoxError) as exc:
        read_yaml_document(p)
    assert code(exc) == expected


def test_utf8(tmp_path):
    p = tmp_path / "bad.cox"
    p.write_bytes(b"\xff")
    with pytest.raises(CoxError) as exc:
        read_yaml_document(p)
    assert code(exc) == "UTF8_INVALID"


@pytest.mark.parametrize(
    "key,value",
    [
        ("Pages", None),
        ("Pages", []),
        ("CoxVersion", 1),
        ("Schema", "invented"),
        ("FileType", "component_spec"),
    ],
)
def test_bad_manifest_is_diagnostic(project, key, value):
    change(project, "manifest.cox", lambda d: d.update({key: value}))
    result = runner.invoke(app, ["validate", str(project), "--json"])
    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["ok"] is False
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    "path",
    ["../outside", "/tmp/outside", "C:\\outside", "page/../../outside", "missing.md"],
)
def test_reference_boundaries(project, path):
    change(project, "manifest.cox", lambda d: d.update(ReferenceDocs=[path]))
    with pytest.raises(CoxError):
        validate_project(project)


def test_symlink_reference(project, tmp_path):
    other = tmp_path / "other"
    other.write_text("outside")
    (project / "link").symlink_to(other)
    change(project, "manifest.cox", lambda d: d.update(ReferenceDocs=["link"]))
    with pytest.raises(CoxError) as exc:
        validate_project(project)
    assert code(exc) == "PATH_SYMLINK"


@pytest.mark.parametrize(
    "key,value", [("Slug", "wrong"), ("ProjectName", "wrong"), ("PageName", "wrong")]
)
def test_page_binding_consistency(project, key, value):
    change(project, "page/page.cox", lambda d: d.update({key: value}))
    with pytest.raises(CoxError) as exc:
        validate_project(project)
    assert code(exc) == "BINDING_MISMATCH"


def test_shared_component_outside_page_directory(project):
    shutil.move(str(project / "page/action_button"), project / "shared")

    def update(d):
        c = d["Pages"][0]["Components"][0]
        c.update(
            Folder="shared",
            ComponentInstruction="shared/action_button.cox",
            ComponentScreenshotPlaceholder="shared/reference.svg",
        )

    change(project, "manifest.cox", update)
    change(
        project,
        "page/page.cox",
        lambda d: d["Children"]["Components"][0].update(Folder="../shared"),
    )
    assert len(validate_project(project).documents) == 3


def test_duplicate_components_and_evidence_typos(project):
    change(
        project,
        "manifest.cox",
        lambda d: d["Pages"][0]["Components"].append(
            d["Pages"][0]["Components"][0].copy()
        ),
    )
    with pytest.raises(CoxError) as exc:
        validate_project(project)
    assert code(exc) == "SLUG_DUPLICATE"
    change(project, "manifest.cox", lambda d: d["Pages"][0]["Components"].pop())
    change(
        project,
        "page/action_button/action_button.cox",
        lambda d: d["EvidenceSummary"].update(Visble=["typo"]),
    )
    with pytest.raises(CoxError) as exc:
        validate_project(project)
    assert code(exc) == "SCHEMA_INVALID"


def test_protocol_and_crop_document_types(project):
    protocol = {
        "CoxVersion": "1.0",
        "FileType": "protocol_doc",
        "Slug": "guide",
        "Schema": "cox.protocol.v1",
        "ProtocolName": "Guide",
        "Purpose": "Example",
    }
    assert not schema_issues(protocol, Path("guide.cox"))
    import yaml

    template = (
        (ROOT / "templates/crop_metadata.cox.template")
        .read_text()
        .replace("{component_slug}", "action_button")
    )
    crop = yaml.safe_load(template)
    # Fill authoring placeholders before validating the concrete document.
    assert not schema_issues(crop, Path("crop_metadata.cox"))
    (project / "guide.cox").write_text(yaml.safe_dump(protocol))
    (project / "crop.cox").write_text(yaml.safe_dump(crop))
    change(
        project,
        "manifest.cox",
        lambda d: d.update(ProtocolDocs=["guide.cox"], GuideDocs=["crop.cox"]),
    )
    assert len(validate_project(project).documents) == 5


def test_init_and_strict_warnings(tmp_path):
    root = init_project(tmp_path / "new", "New Project")
    assert validate_project(root).warnings == []
    with pytest.raises(CoxError):
        init_project(root)
    original = (root / "manifest.cox").read_bytes()
    (root / "extra.cox").write_text("unreferenced: true")
    result = runner.invoke(app, ["validate", str(root), "--json", "--strict"])
    assert result.exit_code == 1
    assert json.loads(result.output)["errors"][0]["code"] == "WARNINGS_AS_ERRORS"
    assert (root / "manifest.cox").read_bytes() == original
    with pytest.raises(CoxError):
        init_project(tmp_path / "bad", "../bad")
    assert not (tmp_path / "bad").exists()


def test_directory_collections_cannot_load_symlink_documents(project, tmp_path):
    outside = tmp_path / "outside.cox"
    outside.write_text("This file must never be parsed")
    folder = project / "guides"
    folder.mkdir()
    (folder / "alias.cox").symlink_to(outside)
    change(project, "manifest.cox", lambda d: d.update(GuideDocs=["guides"]))
    with pytest.raises(CoxError) as exc:
        validate_project(project)
    assert code(exc) == "PATH_SYMLINK"


@pytest.mark.parametrize("name", ["CON", "aux.txt", "trailing.", "   ", "with/slash"])
def test_init_rejects_nonportable_names(tmp_path, name):
    with pytest.raises(CoxError):
        init_project(tmp_path / "new", name)
    assert not (tmp_path / "new").exists()
