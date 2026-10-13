import json

from amc_wx_lite.version_info import (
    is_main_window_title,
    read_build_label,
    window_title,
)


def test_window_title_identifies_the_exact_bundle(tmp_path) -> None:
    (tmp_path / "bundle-manifest.json").write_text(
        json.dumps({"buildLabel": "2026.10.13-7c246dba-a1b2c3d4"}),
        encoding="utf-8",
    )

    assert window_title(tmp_path) == (
        "AMC Python — wersja 0.1.0, kompilacja 2026.10.13-7c246dba-a1b2c3d4"
    )


def test_invalid_manifest_never_leaks_technical_content(tmp_path) -> None:
    (tmp_path / "bundle-manifest.json").write_text(
        '{"buildLabel":"RuntimeObject { Id = tajne }"}',
        encoding="utf-8",
    )

    assert read_build_label(tmp_path) == ""
    assert window_title(tmp_path) == "AMC Python — wersja 0.1.0"


def test_main_window_matcher_excludes_diagnostic_alert() -> None:
    assert is_main_window_title("AMC Python")
    assert is_main_window_title(
        "AMC Python — wersja 0.1.0, kompilacja 2026.10.13-7c246db"
    )
    assert not is_main_window_title("Diagnostyka AMC Python")
