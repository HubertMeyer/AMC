"""YT-001: konto Google, bezpieczne etykiety i jeden model poleceń."""

from __future__ import annotations

from pathlib import Path

from amc_wx_lite.command_palette import entries_for_session
from amc_wx_lite.host_client import LiteHostClient
from amc_wx_lite import menu_model
from amc_wx_lite.navigation import SessionId
from amc_wx_lite.release_profile import PUBLIC_PROFILE, TEST_PROFILE
from amc_wx_lite.shortcuts import Action, describe
from amc_wx_lite.youtube_account import (
    CLIENT_ID_ENVIRONMENT,
    account_connected,
    resolve_youtube_client_id,
    safe_message,
    sync_preview,
)


CLIENT_ID = "123456789012-example.apps.googleusercontent.com"


def test_oauth_configuration_is_test_only_and_validated(tmp_path: Path) -> None:
    assert resolve_youtube_client_id(
        {CLIENT_ID_ENVIRONMENT: CLIENT_ID}, profile=TEST_PROFILE
    ) == CLIENT_ID
    assert resolve_youtube_client_id(
        {CLIENT_ID_ENVIRONMENT: CLIENT_ID}, profile=PUBLIC_PROFILE
    ) is None
    assert resolve_youtube_client_id(
        {CLIENT_ID_ENVIRONMENT: "niedozwolony identyfikator"},
        profile=TEST_PROFILE,
        resource_path=tmp_path / "brak.txt",
    ) is None

    resource = tmp_path / "youtube-oauth-client-id.txt"
    resource.write_text(CLIENT_ID + "\n", encoding="utf-8")
    assert resolve_youtube_client_id(
        {}, profile=TEST_PROFILE, resource_path=resource
    ) == CLIENT_ID


def test_protocol_payload_never_becomes_object_representation() -> None:
    payload = {
        "connected": True,
        "message": "  YouTube:\n zalogowano  ",
        "channelLabels": [
            " Kanał\r\nPierwszy ",
            {"title": "rekord techniczny"},
            "Kanał Drugi",
        ],
        "additions": 2,
        "restores": 0,
        "alreadyPresent": 4,
        "suppressed": 1,
        "channelId": "UC-TAJNY-TECHNICZNY",
    }
    preview = sync_preview(payload)

    assert account_connected(payload) is True
    assert safe_message(payload, "brak") == "YouTube: zalogowano"
    assert preview is not None
    assert preview.labels == ("Kanał Pierwszy", "Kanał Drugi")
    assert preview.additions == 2 and preview.already_present == 4
    assert "UC-TAJNY" not in " ".join(preview.labels)
    assert safe_message(object(), "Bezpieczny komunikat") == "Bezpieczny komunikat"


def test_host_client_has_explicit_youtube_operations_and_public_client_id() -> None:
    client = LiteHostClient(Path("host.exe"), youtube_client_id=CLIENT_ID)
    command = client._command()
    assert command[-2:] == ["--youtube-client-id", CLIENT_ID]

    calls: list[tuple[str, object, float]] = []

    def call(operation: str, args: object = None, timeout: float = 10.0) -> dict:
        calls.append((operation, args, timeout))
        return {"message": "ok"}

    client.call = call  # type: ignore[method-assign]
    client.youtube_account_capabilities()
    client.youtube_account_status()
    client.youtube_account_login()
    client.youtube_account_cancel_login()
    client.youtube_account_logout()
    client.youtube_subscription_sync_preview(restore_suppressed=True)
    client.youtube_subscription_sync_apply(restore_suppressed=False)

    assert [entry[0] for entry in calls] == [
        "youtube.accountCapabilities",
        "youtube.accountStatus",
        "youtube.accountLogin",
        "youtube.accountCancelLogin",
        "youtube.accountLogout",
        "youtube.subscriptionSyncPreview",
        "youtube.subscriptionSyncApply",
    ]
    assert calls[-2][1] == {"restoreSuppressed": True}
    assert calls[-1][1] == {"restoreSuppressed": False}


def test_runtime_capability_controls_menu_palette_and_help_together() -> None:
    hidden = menu_model.menus_for_session(SessionId.PODCASTS)
    visible = menu_model.menus_for_session(
        SessionId.PODCASTS,
        youtube_account_available=True,
    )
    assert not any(
        item.action is Action.YOUTUBE_ACCOUNT
        for menu in hidden
        for item in menu.items
    )
    assert sum(
        item.action is Action.YOUTUBE_ACCOUNT
        for menu in visible
        for item in menu.items
    ) == 1
    assert not any(
        item.action is Action.YOUTUBE_ACCOUNT
        for item in entries_for_session(SessionId.PODCASTS)
    )
    entry = next(
        item
        for item in entries_for_session(
            SessionId.PODCASTS,
            youtube_account_available=True,
        )
        if item.action is Action.YOUTUBE_ACCOUNT
    )
    assert entry.name == "Konto YouTube i synchronizacja subskrypcji…"
    assert dict(describe("Podcasty i YouTube", {Action.YOUTUBE_ACCOUNT})) == {
        "Bez skrótu": "Konto YouTube i synchronizacja subskrypcji"
    }


def test_dialog_source_has_intentional_accessible_labels() -> None:
    source = (Path(__file__).parents[1] / "amc_wx_lite" / "gui.py").read_text(
        encoding="utf-8"
    )
    dialog = source[
        source.index("class YouTubeAccountDialog") :
        source.index("class SonosAccountDialog")
    ]
    for label in (
        "Stan konta YouTube",
        "Kanały planowane do zapisania w Bibliotece AMC",
        "Zaloguj konto YouTube przez Google w przeglądarce",
        "Anuluj oczekiwanie na logowanie YouTube",
        "Zamknij okno konta YouTube",
    ):
        assert label in dialog
    assert "str(payload)" not in dialog
    assert "repr(" not in dialog
