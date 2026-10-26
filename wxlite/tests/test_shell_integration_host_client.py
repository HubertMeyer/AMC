from __future__ import annotations

from pathlib import Path

from amc_wx_lite.host_client import LiteHostClient


def test_shell_integration_uses_three_narrow_named_operations() -> None:
    calls: list[tuple[str, dict | None, float]] = []
    client = LiteHostClient(Path("host.exe"))
    client.call = lambda op, args=None, *, timeout=20.0: (
        calls.append((op, args, timeout)) or {"success": True}
    )

    client.shell_integration_status()
    client.general_settings_defaults()
    client.apply_shell_integration(
        context_menu_enabled=True,
        open_with_enabled=False,
        group_ids=["common-audio", "playlists", "common-audio"],
    )
    client.open_windows_default_apps()

    assert calls == [
        ("shellIntegration.status", None, 20.0),
        ("settings.defaults", None, 20.0),
        (
            "shellIntegration.apply",
            {
                "contextMenuEnabled": True,
                "openWithEnabled": False,
                "groupIds": ["common-audio", "playlists"],
            },
            30.0,
        ),
        ("shellIntegration.openDefaultApps", None, 20.0),
    ]
