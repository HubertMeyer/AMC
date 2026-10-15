from amc_wx_lite.item_information import item_properties_text
from amc_wx_lite.list_model import Row


def test_item_properties_use_only_user_facing_fields() -> None:
    row = Row(
        item_id="internal-row-id",
        service_id="service:technical-id",
        title="Przykładowy utwór",
        kind="track",
        path=r"D:\Muzyka\utwor.flac",
        detail="FLAC, stereo",
        state_detail="odtwarzanie",
        artist_name="Przykładowy wykonawca",
        related_album_title="Przykładowy album",
        duration_ticks=125 * 10_000_000,
        position_seconds=15,
    )

    text = item_properties_text(
        row,
        session_label="Pliki lokalne",
        view_label="Wszystkie pliki",
    )

    assert "Nazwa: Przykładowy utwór" in text
    assert "Rodzaj: utwór" in text
    assert "Wykonawca: Przykładowy wykonawca" in text
    assert "Czas trwania:" in text
    assert r"Ścieżka: D:\Muzyka\utwor.flac" in text
    assert "internal-row-id" not in text
    assert "service:technical-id" not in text


def test_item_properties_use_address_for_stream_without_path() -> None:
    text = item_properties_text(
        Row(
            item_id="station-1",
            title="Radio Test",
            kind="station",
            url="https://example.test/live",
        ),
        session_label="Radio internetowe",
    )

    assert "Adres: https://example.test/live" in text
    assert "Ścieżka:" not in text
