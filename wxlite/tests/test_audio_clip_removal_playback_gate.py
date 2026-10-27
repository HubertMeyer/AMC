"""Kontrakt zwalniania dekodera i blokady odtwarzania przy wycinaniu.

To regresja bledu z 27.10.2026: ``Stop`` wyciszal plik, ale domykal dekoder
w tle, a ponowne ``files.play`` moglo otworzyc ten sam plik w czasie, gdy
edytor czekal na dostep wylaczny.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLERS = ROOT / "src" / "AccessibleMediaController.LiteHost" / "LiteEngineHandlers.cs"
OUTPUT = ROOT / "src" / "AccessibleMediaController.Windows" / "Services" / "WindowsMediaOutput.cs"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_local_playback_commands_share_the_audio_edit_gate() -> None:
    source = _text(HANDLERS)
    for operation in ("files.play", "media.play", "queue.playAt", "queue.next", "queue.previous"):
        start = source.index(f'["{operation}"]')
        fragment = source[start : start + 220]
        assert "RunLocalPlaybackStart" in fragment, operation

    assert 'RunLocalPlaybackStart(() => PauseResumeResolved(target))' in source
    assert 'RunLocalPlaybackStart(() => SelectOutputResolved(args, sessionId))' in source
    assert "if (_audioClipRemovalInProgress) return;" in source
    assert "next = _queue.HandlePlaybackEnded(e.Item.Id);" in source
    assert "Trwa usuwanie fragmentu." in source


def test_remove_waits_for_its_own_decoder_and_always_releases_gate() -> None:
    source = _text(HANDLERS)
    start = source.index("private object RemoveAudioClip")
    end = source.index("private object AppendAudioClip", start)
    body = source[start:end]

    armed = body.index("_audioClipRemovalInProgress = true")
    stopped = body.index("StopFilesPlayback()")
    waited = body.index("WaitForPendingPipelineDisposalAsync")
    edited = body.index("LiteAudioClipOperations.Remove")
    released_after_stop_failure = body.index("_audioClipRemovalInProgress = false")
    released = body.rindex("_audioClipRemovalInProgress = false")
    assert armed < stopped < waited < edited < released
    assert stopped < released_after_stop_failure < waited
    assert "finally" in body


def test_media_output_tracks_background_pipeline_disposal() -> None:
    source = _text(OUTPUT)
    assert "private Task _lastPipelineDisposalTask = Task.CompletedTask" in source
    assert "public async Task WaitForPendingPipelineDisposalAsync" in source
    assert "_lastPipelineDisposalTask = disposalTask" in source
    assert "Oryginalny plik nie został zmieniony" in source
