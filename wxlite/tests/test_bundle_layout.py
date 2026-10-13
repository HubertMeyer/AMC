"""Package layout checks on explicit synthetic files; not an executable test."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone

path = Path(__file__).resolve().parents[1] / "tools" / "build_bundle.py"
spec = importlib.util.spec_from_file_location("lite_bundle_under_test", path)
assert spec is not None and spec.loader is not None
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


def test_python_package_matches_isolated_runtime_app_path():
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder)
        bundle.copy_python_code(target)
        assert (target / "app" / "amc_wx_lite" / "__main__.py").is_file()
        assert not (target / "AMC-wx-Lite.cmd").exists()


def test_build_label_is_user_facing_date_and_source_revision():
    class Result:
        def __init__(self, stdout):
            self.stdout = stdout

    original = bundle.subprocess.run
    try:
        bundle.subprocess.run = lambda args, **kwargs: Result(
            "7C246DBA1234567890ABCDEF1234567890ABCDEF\n"
            if "rev-parse" in args else ""
        )
        label = bundle.build_label(
            datetime(2026, 10, 13, tzinfo=timezone.utc),
            content_id="A1B2C3D4",
        )
    finally:
        bundle.subprocess.run = original
    assert label == (
        "2026.10.13-7c246dba1234567890abcdef1234567890abcdef-a1b2c3d4"
    )


def test_source_identity_marks_untracked_source_as_working_copy():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "AMC test"],
            cwd=root,
            check=True,
        )
        tracked = root / "tracked.txt"
        tracked.write_text("zatwierdzone", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
        (root / "new-source.py").write_text("print('nowe')", encoding="utf-8")

        original_repo = bundle.REPO
        try:
            bundle.REPO = root
            revision, dirty = bundle.git_source_identity()
        finally:
            bundle.REPO = original_repo

        assert len(revision) == 40
        assert dirty is True


def test_source_identity_ignores_only_release_scratch_directories():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "AMC test"],
            cwd=root,
            check=True,
        )
        tracked = root / "tracked.txt"
        tracked.write_text("zatwierdzone", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
        output = root / ".test-output" / "candidate" / "artifact.bin"
        temporary = root / ".test-tmp" / "probe" / "trace.txt"
        output.parent.mkdir(parents=True)
        temporary.parent.mkdir(parents=True)
        output.write_bytes(b"artifact")
        temporary.write_text("trace", encoding="utf-8")

        original_repo = bundle.REPO
        try:
            bundle.REPO = root
            revision, dirty = bundle.git_source_identity()
        finally:
            bundle.REPO = original_repo

        assert len(revision) == 40
        assert dirty is False


def test_build_label_marks_tracked_changes_as_working_copy():
    assert bundle.build_label(
        datetime(2026, 10, 14, tzinfo=timezone.utc),
        revision="1fe0f900",
        dirty=True,
        content_id="a1b2c3d4",
    ) == "2026.10.14-1fe0f900-a1b2c3d4-robocza"


def test_bundle_identity_changes_when_any_packaged_file_changes():
    first = bundle.bundle_identity({"AMC.exe": "a" * 64})
    second = bundle.bundle_identity({"AMC.exe": "b" * 64})
    assert first != second


def test_refresh_mode_updates_the_visible_build_identity():
    source = path.read_text(encoding="utf-8")
    assert 'manifest["bundleId"] = bundle_identity(manifest["fileHashes"])' in source
    assert 'manifest["buildLabel"] = build_label(' in source


def test_promotion_verifies_full_candidate_and_installed_package():
    promotion = (
        path.parent / "Promote-AMCPythonTestBuild.ps1"
    ).read_text(encoding="utf-8")
    assert "--untracked-files=all" in promotion
    assert "Test-BundleIntegrity -Root $candidateRoot" in promotion
    assert "Test-BundleIntegrity -Root $InstallRoot" in promotion
    assert "$expectedRuntime" in promotion
    assert "runningExecutable" in promotion


def test_production_launcher_is_copied_as_canonical_entry_point():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        source, target = root / "publish", root / "bundle"
        source.mkdir()
        (source / "AMC.exe").write_bytes(b"SYNTHETIC_LAUNCHER")
        copied = bundle.copy_launcher(target, source)
        assert copied == ["AMC.exe"]
        assert (target / "AMC.exe").read_bytes() == b"SYNTHETIC_LAUNCHER"


def test_startup_file_selection_covers_interface_launcher_and_host():
    files = [
        "AMC.exe",
        "AMC-Python-Updater.exe",
        "app/amc_wx_lite/__main__.py",
        "runtime/python.exe",
        "runtime/pythonw.exe",
        "runtime/LICENSE.txt",
        "host/amc_lite_host.exe",
        "host/AccessibleMediaController.Core.dll",
        "host/readme.md",
    ]
    selected = bundle.select_startup_files(files, "host")
    assert "AMC.exe" in selected
    assert "app/amc_wx_lite/__main__.py" in selected
    assert "runtime/python.exe" in selected
    assert "runtime/pythonw.exe" in selected
    assert "host/amc_lite_host.exe" in selected
    assert "host/AccessibleMediaController.Core.dll" in selected
    assert "AMC-Python-Updater.exe" not in selected
    assert "host/readme.md" not in selected


def test_dependency_licenses_are_not_dropped_from_host_package():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        source, target = root / "host", root / "bundle"
        (source / "licenses" / "tempo-engines").mkdir(parents=True)
        (source / "amc_lite_host.exe").write_bytes(b"SYNTHETIC_LAYOUT_FIXTURE_NOT_EXECUTABLE")
        (source / "licenses" / "tempo-engines" / "license.txt").write_text("Synthetic license marker")
        copied, _ = bundle.copy_host(target, source)
        assert (target / "host" / "licenses" / "tempo-engines" / "license.txt").read_text() == "Synthetic license marker"
        assert "host/licenses/tempo-engines/license.txt" in copied


def test_host_can_be_staged_without_touching_running_host_folder():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        source, target = root / "source", root / "bundle"
        source.mkdir()
        (source / "amc_lite_host.exe").write_bytes(b"NEW_SYNTHETIC_HOST")
        old_host = target / "host"
        old_host.mkdir(parents=True)
        old_executable = old_host / "amc_lite_host.exe"
        old_executable.write_bytes(b"RUNNING_SYNTHETIC_HOST")

        copied, _ = bundle.copy_host(target, source, "host-next")

        assert old_executable.read_bytes() == b"RUNNING_SYNTHETIC_HOST"
        assert (target / "host-next" / "amc_lite_host.exe").read_bytes() == b"NEW_SYNTHETIC_HOST"
        assert "host-next/amc_lite_host.exe" in copied


def test_host_subfolder_rejects_path_traversal():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "source"
        source.mkdir()
        (source / "amc_lite_host.exe").write_bytes(b"SYNTHETIC")
        try:
            bundle.copy_host(root / "bundle", source, "../outside")
        except SystemExit as error:
            assert "bezpieczna nazwa" in str(error)
        else:
            raise AssertionError("folder hosta nie moze wychodzic poza pakiet")


def test_embedded_path_is_patched_in_copy_not_source():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        runtime = root / "source"
        runtime.mkdir()
        text = "python314.zip\n.\nLib/site-packages\n"
        (runtime / "python314._pth").write_text(text)
        bundle.copy_runtime(root / "bundle", runtime)
        assert "../app" in (root / "bundle" / "runtime" / "python314._pth").read_text().splitlines()
        assert (runtime / "python314._pth").read_text() == text


def test_runtime_can_be_reused_in_place_during_bundle_update():
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "bundle"
        runtime = target / "runtime"
        runtime.mkdir(parents=True)
        marker = runtime / "python.exe"
        marker.write_bytes(b"sprawdzony-runtime")
        copied = bundle.copy_runtime(target, runtime)
        assert marker.read_bytes() == b"sprawdzony-runtime"
        assert "runtime/python.exe" in copied
