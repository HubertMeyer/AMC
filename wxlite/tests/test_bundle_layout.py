"""Package layout checks on explicit synthetic files; not an executable test."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
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
        assert (target / "app" / "amc_wx_lite" / "spotify_source.py").is_file()
        assert (target / "app" / "amc_wx_lite" / "tidal_source.py").is_file()
        assert (target / "app" / "amc_wx_lite" / "sonos_source.py").is_file()
        assert not (target / "AMC-wx-Lite.cmd").exists()


def test_public_python_package_omits_and_removes_private_service_modules():
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder)
        package = target / "app" / "amc_wx_lite"
        package.mkdir(parents=True)
        for name in bundle.PRIVATE_SERVICE_MODULES:
            (package / name).write_text("stary prywatny modul", encoding="utf-8")

        copied = bundle.copy_python_code(target, bundle.profile_from_id("public"))

        assert "app/amc_wx_lite/gui.py" in copied
        for name in bundle.PRIVATE_SERVICE_MODULES:
            assert not (package / name).exists()
            assert f"app/amc_wx_lite/{name}" not in copied


def test_public_gui_imports_without_private_service_modules():
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder)
        bundle.copy_python_code(target, bundle.profile_from_id("public"))
        environment = dict(os.environ)
        environment["AMC_RELEASE_PROFILE"] = "public"
        environment["PYTHONPATH"] = str(target / "app")

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import amc_wx_lite.gui as gui; "
                    "assert gui._RELEASE_PROFILE.profile_id == 'public'; "
                    "assert not hasattr(gui, 'TidalSource'); "
                    "assert not hasattr(gui, 'SpotifyPlaylistDialog'); "
                    "assert not hasattr(gui, 'SonosPayloadError')"
                ),
            ],
            cwd=target,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr or result.stdout


def test_bundle_manifest_profile_is_explicit_and_public_is_restricted():
    public = bundle.profile_from_id("public")
    manifest = bundle.initial_manifest(public, "a" * 40, False)

    assert manifest["releaseProfileSchema"] == 1
    assert manifest["releaseProfile"] == "public"
    assert manifest["displayName"] == "AMC"
    assert manifest["installId"] == "AMC.Public.win-x64"
    assert manifest["updateChannel"] == "stable"
    assert manifest["sessions"] == ["files", "radio", "podcasts", "wiim"]
    assert "spotify" not in " ".join(manifest["capabilities"]).casefold()
    assert manifest["credentialNamespace"] != (
        bundle.profile_from_id("test").credential_namespace
    )


def test_public_profile_rejects_any_listed_librespot_component():
    public = bundle.profile_from_id("public")
    try:
        bundle.validate_profile_files(
            public,
            ["host/LibrespotHost/amc_spotify_librespot_host.exe"],
        )
    except SystemExit as error:
        assert "Publiczny pakiet AMC" in str(error)
    else:
        raise AssertionError("Publiczny profil nie moze zawierac hosta Librespot")


def test_public_profile_rejects_any_listed_private_service_module():
    public = bundle.profile_from_id("public")
    for name in bundle.PRIVATE_SERVICE_MODULES:
        try:
            bundle.validate_profile_files(public, [f"app/amc_wx_lite/{name}"])
        except SystemExit as error:
            assert "Publiczny pakiet AMC" in str(error)
        else:
            raise AssertionError(
                f"Publiczny profil nie moze zawierac prywatnego modulu {name}"
            )


def test_file_integrity_contains_hash_and_exact_size_for_every_file():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "one.bin").write_bytes(b"1234")
        (root / "two.bin").write_bytes(b"abc")
        manifest = {"files": ["one.bin", "two.bin", "one.bin"]}
        bundle.add_file_integrity(manifest, root)
        assert manifest["files"] == ["one.bin", "two.bin"]
        assert set(manifest["fileHashes"]) == set(manifest["files"])
        assert manifest["fileSizes"] == {"one.bin": 4, "two.bin": 3}


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
        "host/LibrespotHost/amc_spotify_librespot_host.exe",
        "host/LibrespotHost/provenance-amc-host.json",
        "host/readme.md",
    ]
    selected = bundle.select_startup_files(files, "host")
    assert "AMC.exe" in selected
    assert "app/amc_wx_lite/__main__.py" in selected
    assert "runtime/python.exe" in selected
    assert "runtime/pythonw.exe" in selected
    assert "host/amc_lite_host.exe" in selected
    assert "host/AccessibleMediaController.Core.dll" in selected
    assert "host/LibrespotHost/amc_spotify_librespot_host.exe" in selected
    assert "host/LibrespotHost/provenance-amc-host.json" in selected
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


def test_pinned_librespot_source_matches_local_provenance_and_license_inventory():
    provenance = bundle.validate_librespot_package_source()
    assert provenance["sha256"] == bundle.LIBRESPOT_HOST_SHA256
    assert provenance["amcCommit"] == bundle.LIBRESPOT_AMC_COMMIT
    assert provenance["librespotRev"] == bundle.LIBRESPOT_REVISION
    assert provenance["runUrl"] == bundle.LIBRESPOT_RUN_URL


def test_librespot_provenance_mismatch_refuses_before_writing_package():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "source"
        licenses = root / "licenses"
        dependencies = licenses / "librespot-dependencies"
        source.mkdir()
        dependencies.mkdir(parents=True)
        shutil.copy2(
            bundle.LIBRESPOT_HOST_SOURCE / bundle.LIBRESPOT_HOST_BINARY,
            source / bundle.LIBRESPOT_HOST_BINARY,
        )
        provenance = json.loads(
            (
                bundle.LIBRESPOT_HOST_SOURCE / bundle.LIBRESPOT_HOST_PROVENANCE
            ).read_text(encoding="utf-8")
        )
        provenance["sha256"] = "0" * 64
        (source / bundle.LIBRESPOT_HOST_PROVENANCE).write_text(
            json.dumps(provenance), encoding="utf-8"
        )
        (licenses / "librespot-MIT.txt").write_text(
            "MIT License\nCopyright (c) 2015 Paul Lietar\n", encoding="utf-8"
        )
        (dependencies / "INDEX.txt").write_text(
            f"365 paczek\n{bundle.LIBRESPOT_REVISION}\n", encoding="utf-8"
        )
        (dependencies / "inventory.json").write_text(
            json.dumps([{"verified": True}] * 365), encoding="utf-8"
        )

        target = root / "bundle"
        try:
            bundle.copy_librespot_host(target, source_dir=source, licenses_dir=licenses)
        except SystemExit as error:
            assert "Niespojna proweniencja" in str(error)
        else:
            raise AssertionError("Niespojna proweniencja nie moze trafic do paczki")
        assert not target.exists()


def test_full_bundle_validates_librespot_before_cleaning_existing_candidate():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        target = root / "bundle"
        runtime = root / "runtime"
        target.mkdir()
        runtime.mkdir()
        marker = target / "do-not-touch.txt"
        marker.write_text("poprzedni kandydat", encoding="utf-8")

        original_argv = sys.argv
        original_validator = bundle.validate_librespot_package_source
        try:
            sys.argv = [
                str(path),
                "--out", str(target),
                "--runtime", str(runtime),
                "--clean",
            ]

            def refuse(*_args, **_kwargs):
                raise SystemExit("Niespojna proweniencja")

            bundle.validate_librespot_package_source = refuse
            try:
                bundle.main()
            except SystemExit as error:
                assert "Niespojna proweniencja" in str(error)
            else:
                raise AssertionError("Pelna paczka musi odmowic niespojnego hosta")
        finally:
            bundle.validate_librespot_package_source = original_validator
            sys.argv = original_argv

        assert marker.read_text(encoding="utf-8") == "poprzedni kandydat"


def test_full_bundle_places_pinned_librespot_relative_to_lite_host_and_hashes_it():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        host = root / "host-publish"
        launcher = root / "launcher-publish"
        updater = root / "updater-publish"
        runtime = root / "runtime-source"
        unrelated_cwd = root / "unrelated-cwd"
        target = root / "bundle"
        for directory in (host, launcher, updater, runtime, unrelated_cwd):
            directory.mkdir()
        (host / "amc_lite_host.exe").write_bytes(b"SYNTHETIC_LITE_HOST")
        (launcher / "AMC.exe").write_bytes(b"SYNTHETIC_LAUNCHER")
        (updater / "AMC-Python-Updater.exe").write_bytes(b"SYNTHETIC_UPDATER")
        (runtime / "python.exe").write_bytes(b"SYNTHETIC_PYTHON")
        (runtime / "pythonw.exe").write_bytes(b"SYNTHETIC_PYTHONW")
        (runtime / "python314._pth").write_text("python314.zip\n", encoding="utf-8")

        original_argv = sys.argv
        original_cwd = Path.cwd()
        try:
            sys.argv = [
                str(path),
                "--out", str(target),
                "--host", str(host),
                "--host-subdir", "host-next",
                "--launcher", str(launcher),
                "--updater", str(updater),
                "--runtime", str(runtime),
            ]
            os.chdir(unrelated_cwd)
            assert bundle.main() == 0
        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv

        manifest_path = target / "bundle-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest_path.stat().st_size < 8 * 1024 * 1024
        executable = (
            "host-next/LibrespotHost/" + bundle.LIBRESPOT_HOST_BINARY
        )
        provenance = (
            "host-next/LibrespotHost/" + bundle.LIBRESPOT_HOST_PROVENANCE
        )
        librespot_manifest = manifest["librespotHost"]
        assert librespot_manifest["executable"] == executable
        assert librespot_manifest["pathFromLiteHostBase"] == (
            "LibrespotHost/" + bundle.LIBRESPOT_HOST_BINARY
        )
        assert librespot_manifest["sha256"] == bundle.LIBRESPOT_HOST_SHA256
        assert librespot_manifest["bytes"] == bundle.LIBRESPOT_HOST_SIZE
        assert librespot_manifest["provenance"] == provenance
        assert manifest["hostHashes"][
            "LibrespotHost/" + bundle.LIBRESPOT_HOST_BINARY
        ] == bundle.LIBRESPOT_HOST_SHA256
        for relative in (
            executable,
            provenance,
            "host-next/licenses/librespot-MIT.txt",
            "host-next/licenses/librespot-dependencies/INDEX.txt",
            "host-next/licenses/librespot-dependencies/inventory.json",
        ):
            assert relative in manifest["files"]
            assert relative in manifest["fileHashes"]
            assert manifest["fileHashes"][relative] == bundle.sha256(target / relative)
            if "/licenses/" in relative:
                assert relative in librespot_manifest["licenseFiles"]
        expected_license_count = 1 + sum(
            1
            for item in (
                bundle.LIBRESPOT_LICENSES_SOURCE / "librespot-dependencies"
            ).rglob("*")
            if item.is_file()
        )
        assert len(librespot_manifest["licenseFiles"]) == expected_license_count
        for relative in librespot_manifest["licenseFiles"]:
            assert relative in manifest["files"]
            assert manifest["fileHashes"][relative] == bundle.sha256(target / relative)
        assert executable in manifest["startupFiles"]
        assert provenance in manifest["startupFiles"]
        assert (target / executable).read_bytes() == (
            bundle.LIBRESPOT_HOST_SOURCE / bundle.LIBRESPOT_HOST_BINARY
        ).read_bytes()


def test_full_public_bundle_omits_librespot_and_has_complete_sizes():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        host = root / "host-publish"
        launcher = root / "launcher-publish"
        updater = root / "updater-publish"
        runtime = root / "runtime-source"
        target = root / "public-bundle"
        for directory in (host, launcher, updater, runtime):
            directory.mkdir()
        (host / "amc_lite_host.exe").write_bytes(b"SYNTHETIC_LITE_HOST")
        (launcher / "AMC.exe").write_bytes(b"SYNTHETIC_LAUNCHER")
        (updater / "AMC-Python-Updater.exe").write_bytes(b"SYNTHETIC_UPDATER")
        (runtime / "python.exe").write_bytes(b"SYNTHETIC_PYTHON")
        (runtime / "pythonw.exe").write_bytes(b"SYNTHETIC_PYTHONW")
        (runtime / "python314._pth").write_text("python314.zip\n", encoding="utf-8")

        original_argv = sys.argv
        original_validator = bundle.validate_librespot_package_source
        try:
            sys.argv = [
                str(path),
                "--out", str(target),
                "--profile", "public",
                "--host", str(host),
                "--launcher", str(launcher),
                "--updater", str(updater),
                "--runtime", str(runtime),
                "--clean",
            ]

            def must_not_read_private_component(*_args, **_kwargs):
                raise AssertionError("Publiczny build odczytal prywatny host Librespot")

            bundle.validate_librespot_package_source = must_not_read_private_component
            assert bundle.main() == 0
        finally:
            bundle.validate_librespot_package_source = original_validator
            sys.argv = original_argv

        manifest = json.loads(
            (target / "bundle-manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["releaseProfile"] == "public"
        assert "librespotHost" not in manifest
        assert not any("librespot" in relative.casefold() for relative in manifest["files"])
        assert not any(
            Path(relative).name in bundle.PRIVATE_SERVICE_MODULES
            for relative in manifest["files"]
        )
        assert set(manifest["fileHashes"]) == set(manifest["files"])
        assert set(manifest["fileSizes"]) == set(manifest["files"])
        for relative in manifest["files"]:
            file_path = target / relative
            assert manifest["fileSizes"][relative] == file_path.stat().st_size
            assert manifest["fileHashes"][relative] == bundle.sha256(file_path)
