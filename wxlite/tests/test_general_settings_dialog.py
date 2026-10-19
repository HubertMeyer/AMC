"""Structural contract for the native, keyboard-oriented settings window."""

from __future__ import annotations

from pathlib import Path


SOURCE = Path(__file__).parents[1] / "amc_wx_lite" / "gui.py"


def test_settings_have_real_native_pages_and_explicit_accessible_names() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "self.notebook = wx.Notebook(self)" in source
    assert 'self.notebook.SetName("Kategorie ustawień")' in source
    assert 'self.notebook.AddPage(general, "Ogólne", select=True)' in source
    assert 'self.notebook.AddPage(radio, "Radio i nagrywanie")' in source
    assert 'self.notebook.AddPage(podcasts, "Podcasty i YouTube")' in source
    assert 'self.notebook.AddPage(messages, "Komunikaty")' in source
    assert 'self.startup_target.SetName("Wyświetlaj po uruchomieniu")' in source
    assert 'choices=["Ostatnia używana sesja", "Menedżer sesji"]' in source
    assert 'self.silence.SetName("Dodatkowa cisza po naturalnym końcu utworu")' in source
    assert 'self.tempo.SetName("Sposób przeliczania zmienionego tempa")' in source
    assert 'self.keep_audio_edit_backups.SetName("Zachowuj kopie po edycji")' in source
    assert '"Długość przeskoku pod Ctrl+Alt+strzałką w lewo i w prawo"' in source
    assert 'self.global_transient_previews.SetName(' in source
    assert '"Wspólne podglądy nagrywania i nowych odcinków we wszystkich sesjach"' in source
    assert 'self.remember_local_playback_positions.SetName(' in source
    assert '"Pamiętaj pozycję odtwarzania lokalnych plików"' in source
    assert 'self.detailed_hints.SetName(' in source
    assert '"Pokazuj szczegółowe podpowiedzi klawiatury przy polach i listach"' in source
    assert 'self.message_enabled.SetName("Włącz komunikaty dostępności")' in source
    assert 'self.message_seek_messages.SetName(' in source
    assert '"Włącz automatyczne komunikaty odtwarzacza"' in source
    assert 'self.message_arrow_seek_messages.SetName(' in source
    assert '"Oznajmiaj przewijanie strzałkami oraz klawiszami Home i End"' in source
    assert 'self.message_percentage_seek_messages.SetName(' in source
    assert '"Oznajmiaj skoki klawiszami cyfr"' in source
    assert 'self.message_volume_messages.SetName("Oznajmiaj zmiany głośności")' in source
    assert 'self.message_playback_messages.SetName(' in source
    assert '"Oznajmiaj odtwarzanie i pauzę"' in source
    assert 'self.message_bookmark_navigation_messages.SetName(' in source
    assert '"Oznajmiaj nawigację po zakładkach"' in source
    assert 'self.message_percent_announcement.SetName(' in source
    assert 'choices=["Tylko procent", "Tylko czas", "Procent i czas"]' in source
    assert 'self.message_templates.SetName("Zdarzenia komunikatów")' in source
    assert 'self.message_template_text.SetName(' in source
    assert '"Tekst szablonu wybranego komunikatu"' in source
    assert "choices=[TEMPLATE_LABELS[key]" in source


def test_enter_save_has_one_short_confirmation_and_reconfigures_the_host() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert 'save.SetName("Zapisz ustawienia")' in source
    assert 'save.SetDefault()' in source
    assert 'self.announcer.say("Zapisano ustawienia")' in source
    assert 'client.configure_audio(' in source
    method = source[source.index("def _show_general_playback_options") :]
    method = method[:method.index("def _with_radio_recording_options")]
    assert "dialog.Destroy()\n        self._restore_focus_after_dialog()" in method
    assert method.index('self.announcer.say("Zapisano ustawienia")') < method.index(
        "client = self.client"
    )
    assert method.count('self.announcer.say("Zapisano ustawienia")') == 1


def test_all_exposed_choices_use_intentional_user_facing_labels() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "choices=[TEMPO_LABELS[value] for value in self._tempo_values]" in source
    assert "session_options.inter_track_silence_label(value)" in source
    assert "STATE_POSITION_LABELS" in source
    assert 'self.timeshift.SetName("Długość bufora transmisji")' in source
    assert '"keep_audio_edit_backups": self.keep_audio_edit_backups.GetValue()' in source
    assert '"startup_target": self._startup_target_values[' in source
    assert '"custom_seek_seconds": self._custom_seek_seconds' in source
    assert '"global_transient_previews": self.global_transient_previews.GetValue()' in source
    assert '"remember_local_playback_positions": (' in source
    assert '"detailed_hints": self.detailed_hints.GetValue()' in source
    assert '"message_enabled": self.message_enabled.GetValue()' in source
    assert '"message_seek_messages": self.message_seek_messages.GetValue()' in source
    assert '"message_arrow_seek_messages": (' in source
    assert '"message_percentage_seek_messages": (' in source
    assert '"message_volume_messages": self.message_volume_messages.GetValue()' in source
    assert '"message_playback_messages": (' in source
    assert '"message_bookmark_navigation_messages": (' in source
    assert '"message_percent_announcement": self._message_percent_values[' in source
    assert '"message_templates": dict(self._message_template_values)' in source
    assert 'self.recording_folder.SetName("Domyślny folder nagrywania radia")' in source
    assert 'self.recording_folder_mode.SetName("Położenie nagrań Radia")' in source
    assert '"Ten sam folder co pobieranie Podcastów"' in source
    assert 'self.recording_format.SetName("Format nagrania radia")' in source
    assert 'self.recording_bitrate.SetName("Bitrate nagrania MP3 lub AAC")' in source
    assert 'self.podcast_folder.SetName(' in source
    assert '"Domyślny folder pobierania podcastów"' in source
    assert 'self.podcast_rss_interval.SetName(' in source
    assert 'self.podcast_youtube_interval.SetName(' in source
    assert 'self.podcast_refresh_batch.SetName(' in source


def test_podcast_settings_reach_the_database_owner_and_automatic_refresh() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "client.configure_podcast_global_settings(" in source
    assert "client.refresh_podcasts_automatically" in source
    assert 'self.runner.submit(\n            "podcast-auto-refresh"' in source


def test_radio_settings_reach_recording_and_schedule_payloads() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "preferences_with_overrides(" in source
    assert 'chosen.pop("radio_schedule_wake_override")' in source
    assert "client.sync_radio_schedules(" in source
    assert "options.timeshift_minutes" in source


def test_audio_edit_backup_setting_reaches_both_destructive_edit_paths() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count("resolve_keep_audio_edit_backups(") == 3
    assert source.count("self.options.keep_audio_edit_backups") == 3


def test_custom_seek_setting_is_applied_on_start_and_immediately_after_save() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count("self.messages.custom_seek_seconds = resolve_custom_seek_seconds(") == 2
    assert "parse_custom_seek_length(self.custom_seek.GetValue())" in source
    assert '"Nie zapisano ustawień"' in source


def test_global_preview_setting_gates_shortcuts_before_session_specific_code() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    dispatch = source[source.index("    def _dispatch(self, action: Action)") :]
    dispatch = dispatch[:dispatch.index("    def ", 5)]
    gate = dispatch.index("action in TRANSIENT_PREVIEW_ACTIONS")
    tidal = dispatch.index("self.navigator.active is SessionId.TIDAL")
    assert gate < tidal
    assert source.count("self._global_transient_previews = resolve_global_transient_previews(") == 2


def test_local_resume_setting_reaches_start_save_and_background_checkpoint() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count("self._remember_local_playback_positions = (") == 2
    assert source.count("client.configure_local_resume(") == 2
    assert "self._checkpoint_local_if_due()" in source
    assert '"local-checkpoint"' in source


def test_detailed_hints_setting_updates_filter_and_search_accessible_help() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count("self._detailed_hints = resolve_detailed_hints(") == 2
    assert "self._apply_detailed_hints()" in source
    assert "detailed_hints=self._detailed_hints" in source
    assert "self.query.SetHelpText(" in source
    assert "self.results.SetHelpText(" in source
    assert "self._help_provider = wx.SimpleHelpProvider()" in source
    assert "wx.HelpProvider.Set(self._help_provider)" in source


def test_message_settings_override_the_inherited_policy_and_toggle_persists() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count("apply_message_overrides(") == 2
    assert source.count("enabled=self.options.message_enabled") == 2
    assert source.count("templates=self.options.message_templates") == 2
    assert "self.options.message_seek_messages = self.messages.seek_messages" in source
    assert "if not self._save_state():" in source
    assert "self.messages.announces_playback" in source
    assert "self.announcer.show(message)" in source


def test_session_list_startup_target_opens_only_after_the_host_is_ready() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    startup = source[source.index("    def _start_engine(self)") :]
    startup = startup[:startup.index("    def _on_engine_event")]
    assert 'if self.options.startup_target == "SessionList":' in startup
    assert "wx.CallAfter(self._show_session_list)" in startup
    assert startup.index("self._load_initial_content()") < startup.index(
        "wx.CallAfter(self._show_session_list)"
    )
