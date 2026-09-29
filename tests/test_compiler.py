import json
import shutil
import zipfile
import pytest
from cox_protocol.cox_lib import CoxError, compile_project, validate_project
from cox_protocol.compiler import MARKER
from cox_protocol.package_target import verify_archive, zip_write_bytes
from conftest import change


def tree(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_deterministic_external_build_and_roundtrip(project, tmp_path):
    first = tmp_path / "one"
    second = tmp_path / "two"
    compile_project(project, first, ["all"])
    copy = tmp_path / "renamed-checkout"
    shutil.copytree(project, copy)
    compile_project(copy, second, ["package", "react,json"])
    assert tree(first) == tree(second)
    archive = next((first / "package").glob("*.zip"))
    verified = verify_archive(archive)
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert names == sorted(names)
        assert all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in z.infolist())
        assert any(n.endswith("/build/manifest.compiled.json") for n in names)
        assert any(n.endswith("/build/reports/verification_report.json") for n in names)
        assert not any(
            str(tmp_path) in z.read(n).decode("utf-8", errors="ignore") for n in names
        )
        z.extractall(tmp_path / "unpacked")
    assert verified["fileCount"] == len(names) - 1
    assert len(validate_project(tmp_path / "unpacked/cox_example").documents) == 3


def test_recompile_ownership_and_removed_target(project, tmp_path):
    out = tmp_path / "out"
    compile_project(project, out, ["all"])
    (out / "user-notes.txt").write_text("preserve me")
    compile_project(project, out, ["json"])
    assert not list((out / "react").rglob("*.tsx"))
    assert not list((out / "package").glob("*.zip"))
    assert (out / "user-notes.txt").read_text() == "preserve me"
    owned = out / "normalized/page/page.json"
    owned.write_text("edited by human")
    before = tree(out)
    with pytest.raises(CoxError) as exc:
        compile_project(project, out, ["all"])
    assert exc.value.issues[0].code == "OUTPUT_MODIFIED"
    assert tree(out) == before


def test_unowned_collision_and_output_boundaries(project, tmp_path):
    out = tmp_path / "collision"
    out.mkdir()
    (out / "manifest.compiled.json").write_text("keep")
    with pytest.raises(CoxError):
        compile_project(project, out, ["all"])
    assert tree(out) == {"manifest.compiled.json": b"keep"}
    for path in [project, project.parent, project / "page"]:
        with pytest.raises(CoxError):
            compile_project(project, path, ["json"])
    (tmp_path / "link").symlink_to(out, target_is_directory=True)
    with pytest.raises(CoxError):
        compile_project(project, tmp_path / "link", ["json"])


@pytest.mark.parametrize(
    "raw", ["../victim", "/tmp/victim", "./victim", "a//b", "C:/victim"]
)
def test_invalid_ownership_marker(project, tmp_path, raw):
    out = tmp_path / "out"
    out.mkdir()
    (out / MARKER).write_text(
        json.dumps({"format": "cox-build/1", "files": {raw: "0" * 64}})
    )
    with pytest.raises(CoxError):
        compile_project(project, out, ["json"])


def test_publish_rolls_back_io_failure(project, tmp_path, monkeypatch):
    import cox_protocol.compiler as compiler

    out = tmp_path / "out"
    compile_project(project, out, ["json"])
    before = tree(out)
    change(project, "page/page.cox", lambda d: d["Layout"].update(Desktop="Changed"))
    original = compiler.os.replace
    calls = 0

    def replace(source, dest):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated full disk")
        return original(source, dest)

    monkeypatch.setattr(compiler.os, "replace", replace)
    with pytest.raises(CoxError):
        compile_project(project, out, ["all"])
    assert tree(out) == before


def test_stale_files_not_packaged(project, tmp_path):
    out = project / "build"
    compile_project(project, out, ["all"])
    (out / "stale.txt").write_text("never ship")
    compile_project(project, out, ["package"])
    with zipfile.ZipFile(next((out / "package").glob("*.zip"))) as z:
        assert not any("stale.txt" in n or "/react/" in n for n in z.namelist())


def test_package_excludes_env_and_explicit_transient(project, tmp_path):
    assets = project / "assets"
    assets.mkdir()
    (assets / "readme").write_text("asset")
    (assets / ".env").write_text("not an input")
    change(project, "manifest.cox", lambda d: d.update(ToolingFiles=["assets"]))
    compile_project(project, tmp_path / "out", ["package"])
    with zipfile.ZipFile(next((tmp_path / "out/package").glob("*.zip"))) as z:
        assert not any(n.endswith(".env") for n in z.namelist())
    change(project, "manifest.cox", lambda d: d.update(ToolingFiles=["assets/.env"]))
    with pytest.raises(CoxError):
        compile_project(project, tmp_path / "bad", ["package"])


@pytest.mark.parametrize(
    "mutation", ["tamper", "extra", "duplicate", "traversal", "manifest"]
)
def test_archive_tampering_is_rejected(project, tmp_path, mutation):
    compile_project(project, tmp_path / "out", ["all"])
    original = next((tmp_path / "out/package").glob("*.zip"))
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(bad, "w") as dest:
        for index, info in enumerate(source.infolist()):
            data = source.read(info.filename)
            if mutation == "tamper" and index == 0:
                data += b"tampered"
            if mutation == "manifest" and info.filename.endswith(
                "/package.manifest.json"
            ):
                data = b"{}"
            dest.writestr(info, data)
        if mutation == "extra":
            zip_write_bytes(dest, "cox_example/extra", b"extra")
        if mutation == "traversal":
            zip_write_bytes(dest, "cox_example/../outside", b"outside")
        if mutation == "duplicate":
            with pytest.warns(UserWarning):
                dest.writestr(source.infolist()[0], b"duplicate")
    with pytest.raises(CoxError):
        verify_archive(bad)


def test_react_adversarial_prose_and_numeric_slug(project, tmp_path):
    change(
        project,
        "manifest.cox",
        lambda d: d["Pages"][0]["Components"][0].update(Slug="123_button"),
    )
    change(
        project,
        "page/page.cox",
        lambda d: d["Children"]["Components"][0].update(Slug="123_button"),
    )
    change(
        project,
        "page/action_button/action_button.cox",
        lambda d: d.update(Slug="123_button", Role='a "quote" </section> */\nalert(1)'),
    )
    out = tmp_path / "out"
    compile_project(project, out, ["react"])
    result = (out / "react/components/Cox123Button/index.tsx").read_text()
    assert "export function Cox123Button" in result
    assert 'aria-label={"a \\"quote\\"' in result
    assert "* /" in result


def test_react_collision_is_actionable(project, tmp_path):
    component = project / "page/action_button"
    shutil.copytree(component, project / "page/other")
    change(
        project, "page/other/action_button.cox", lambda d: d.update(Slug="example_page")
    )
    change(
        project,
        "manifest.cox",
        lambda d: d["Pages"][0]["Components"].append(
            {
                "Slug": "example_page",
                "Folder": "page/other",
                "ComponentInstruction": "page/other/action_button.cox",
                "ComponentScreenshotPlaceholder": "page/other/reference.svg",
            }
        ),
    )
    change(
        project,
        "page/page.cox",
        lambda d: d["Children"]["Components"].append(
            {"Slug": "example_page", "Folder": "other", "Role": "Other"}
        ),
    )
    with pytest.raises(CoxError) as exc:
        compile_project(project, tmp_path / "out", ["react"])
    assert exc.value.issues[0].code == "REACT_COLLISION"


def test_modified_marker_or_nested_output_symlink_preserves_files(project, tmp_path):
    out = tmp_path / "out"
    compile_project(project, out, ["json"])
    other = tmp_path / "elsewhere"
    other.mkdir()
    shutil.rmtree(out / "normalized")
    (out / "normalized").symlink_to(other, target_is_directory=True)
    with pytest.raises(CoxError):
        compile_project(project, out, ["json"])
    assert not list(other.iterdir())


def test_unknown_target_does_not_create_outputs(project, tmp_path):
    out = tmp_path / "out"
    with pytest.raises(CoxError) as exc:
        compile_project(project, out, ["all,unknown"])
    assert exc.value.issues[0].code == "TARGET_UNKNOWN"
    assert not out.exists()


def test_output_parent_alias_is_canonicalized_before_overlap_check(project, tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    result = compile_project(project, alias / "output", ["json"])
    assert result["build_root"] == actual / "output"
    assert (actual / "output/manifest.compiled.json").exists()
    project_alias = tmp_path / "project-alias"
    project_alias.symlink_to(project, target_is_directory=True)
    with pytest.raises(CoxError):
        compile_project(project, project_alias / "page", ["json"])
