"""Model okna playlist: jawne etykiety i grupowe członkostwo."""

from __future__ import annotations

from amc_wx_lite.playlist_dialog import (
    PlaylistPayloadError,
    choices_from_payload,
)


def _payload(item_ids: list[str]) -> dict:
    return {
        "sessionId": "local",
        "playlists": [
            {
                "playlistId": "wewnetrzne-id",
                "name": "Poranek",
                "createdUtcTicks": 638000000000000000,
                "itemIds": item_ids,
            }
        ],
    }


def test_mixed_membership_has_an_intentional_accessible_label() -> None:
    choice = choices_from_payload(_payload(["a", "inne"]), ["a", "b"])[0]
    assert choice.membership is None
    assert choice.label == "Poranek, stan mieszany, 2 elementy"
    assert "wewnetrzne-id" not in choice.label
    assert "PlaylistChoice" not in choice.label


def test_space_rule_adds_whole_selection_then_removes_it() -> None:
    choice = choices_from_payload(_payload(["a", "inne"]), ["a", "b"])[0]
    assert choice.toggle(["a", "b"]) is True
    assert choice.item_ids == ["a", "inne", "b"]
    assert choice.label == "Poranek, zaznaczona, 3 elementy"

    assert choice.toggle(["a", "b"]) is False
    assert choice.item_ids == ["inne"]
    assert choice.label == "Poranek, niezaznaczona, 1 element"


def test_malformed_payload_reports_user_facing_error_without_dump() -> None:
    try:
        choices_from_payload({"playlists": [{"playlistId": "sekret"}]}, ["a"])
    except PlaylistPayloadError as error:
        message = str(error)
    else:  # pragma: no cover - zabezpieczenie kontraktu
        raise AssertionError("Uszkodzony wpis powinien zostać odrzucony")
    assert message == "Lista playlist AMC zawiera niepełny wpis"
    assert "sekret" not in message

