"""AMC12: profile wydania sa jawne, odseparowane i steruja mozliwosciami."""

from __future__ import annotations

import os
import importlib
import tempfile
from pathlib import Path

from amc_wx_lite import menu_model
from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.profile_layout import (
    default_amc_local_dir,
    default_amc_profile_dir,
)
from amc_wx_lite.release_profile import (
    PUBLIC_PROFILE,
    TEST_PROFILE,
    current_profile,
    profile_directory,
    profile_from_id,
)
from amc_wx_lite.session_order import (
    SESSION_ACTIONS,
    available_sessions,
    enable,
    manager_labels,
    normalize,
)
from amc_wx_lite.shortcuts import Action
from amc_wx_lite.state_store import default_state_dir


def _with_release_profile(profile_id: str):
    """Maly kontekst bez zaleznosci od pytest i bez wycieku do innych testow."""

    class ProfileEnvironment:
        def __enter__(self):
            self.previous = os.environ.get("AMC_RELEASE_PROFILE")
            os.environ["AMC_RELEASE_PROFILE"] = profile_id
            return self

        def __exit__(self, _type, _value, _traceback):
            if self.previous is None:
                os.environ.pop("AMC_RELEASE_PROFILE", None)
            else:
                os.environ["AMC_RELEASE_PROFILE"] = self.previous

    return ProfileEnvironment()


def test_profiles_have_distinct_identity_storage_channel_and_credentials() -> None:
    assert TEST_PROFILE.display_name == "AMC Test"
    assert PUBLIC_PROFILE.display_name == "AMC"
    assert TEST_PROFILE.product_id != PUBLIC_PROFILE.product_id
    assert TEST_PROFILE.install_id != PUBLIC_PROFILE.install_id
    assert TEST_PROFILE.update_channel != PUBLIC_PROFILE.update_channel
    assert TEST_PROFILE.ui_state_folder != PUBLIC_PROFILE.ui_state_folder
    assert TEST_PROFILE.roaming_profile_folder != PUBLIC_PROFILE.roaming_profile_folder
    assert TEST_PROFILE.local_profile_folder != PUBLIC_PROFILE.local_profile_folder
    assert TEST_PROFILE.cache_folder != PUBLIC_PROFILE.cache_folder
    assert TEST_PROFILE.log_folder != PUBLIC_PROFILE.log_folder
    assert TEST_PROFILE.credential_namespace != PUBLIC_PROFILE.credential_namespace


def test_public_manifest_exposes_only_approved_sessions_and_test_has_all() -> None:
    assert PUBLIC_PROFILE.session_ids == ("files", "radio", "podcasts", "wiim")
    assert set(TEST_PROFILE.session_ids) == {session.value for session in SessionId}
    public_text = " ".join(PUBLIC_PROFILE.capabilities).casefold()
    assert "spotify" not in public_text
    assert "tidal" not in public_text
    assert "sonos" not in public_text


def test_profile_selection_prefers_environment_then_manifest_and_rejects_unknown() -> None:
    with tempfile.TemporaryDirectory(prefix="amc-profile-manifest-") as folder:
        root = Path(folder)
        (root / "bundle-manifest.json").write_text(
            '{"releaseProfileSchema":1,"releaseProfile":"public"}',
            encoding="utf-8",
        )
        assert current_profile({}, root) is PUBLIC_PROFILE
        assert current_profile({"AMC_RELEASE_PROFILE": "test"}, root) is TEST_PROFILE
    try:
        profile_from_id("nieznany")
    except ValueError:
        pass
    else:
        raise AssertionError("Nieznany profil nie moze uruchomic aplikacji")


def test_profile_folders_cannot_escape_system_base() -> None:
    base = Path("C:/Users/test/AppData/Roaming")
    assert profile_directory(base, "AMC/ui") == base / "AMC" / "ui"
    for unsafe in ("../AMC", "/AMC", "AMC/../../inne"):
        try:
            profile_directory(base, unsafe)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Niebezpieczna sciezka zostala przyjeta: {unsafe}")


def test_public_runtime_directories_are_separate_from_test_directories() -> None:
    previous_appdata = os.environ.get("APPDATA")
    previous_local = os.environ.get("LOCALAPPDATA")
    previous_override = os.environ.pop("AMC_WX_LITE_HOME", None)
    os.environ["APPDATA"] = "C:/Users/test/AppData/Roaming"
    os.environ["LOCALAPPDATA"] = "C:/Users/test/AppData/Local"
    try:
        with _with_release_profile("test"):
            test_paths = (
                default_state_dir(),
                default_amc_profile_dir(),
                default_amc_local_dir(),
            )
        with _with_release_profile("public"):
            public_paths = (
                default_state_dir(),
                default_amc_profile_dir(),
                default_amc_local_dir(),
            )
    finally:
        if previous_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = previous_appdata
        if previous_local is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = previous_local
        if previous_override is not None:
            os.environ["AMC_WX_LITE_HOME"] = previous_override
    assert all(test != public for test, public in zip(test_paths, public_paths))


def test_window_identity_uses_user_facing_name_of_selected_profile() -> None:
    from amc_wx_lite import version_info

    try:
        with _with_release_profile("public"):
            public_version = importlib.reload(version_info)
            assert public_version.PRODUCT_NAME == "AMC"
            assert public_version.window_title().startswith("AMC — ")
            assert public_version.is_main_window_title("AMC — wersja 1")
            assert not public_version.is_main_window_title("AMC Test — wersja 1")
    finally:
        importlib.reload(version_info)


def test_public_capability_model_filters_execution_manager_menu_and_palette() -> None:
    raw = [session.value for session in SessionId]
    with _with_release_profile("public"):
        assert available_sessions() == (
            SessionId.FILES,
            SessionId.RADIO,
            SessionId.PODCASTS,
            SessionId.WIIM,
        )
        assert normalize(raw) == available_sessions()
        rows = dict(manager_labels(raw))
        assert set(rows) == set(available_sessions())
        unchanged, message = enable(SessionId.SPOTIFY, raw)
        assert unchanged == available_sessions()
        assert message == "Ta sesja nie jest dostępna w tym wydaniu AMC"

        session_actions = set(SESSION_ACTIONS.values())
        view = next(menu for menu in menu_model.build_menus(raw) if menu.title == "&Widok")
        visible_session_actions = {
            item.action for item in view.items if item.action in session_actions
        }
        assert visible_session_actions == {
            Action.SESSION_FILES,
            Action.SESSION_RADIO,
            Action.SESSION_PODCASTS,
            Action.SESSION_WIIM,
        }
        palette_actions = {
            entry.action for entry in entries_for_session(SessionId.FILES, raw)
        }
        assert visible_session_actions <= palette_actions
        assert Action.SESSION_SPOTIFY not in palette_actions
        assert Action.SESSION_TIDAL not in palette_actions
        assert Action.SESSION_SONOS not in palette_actions
