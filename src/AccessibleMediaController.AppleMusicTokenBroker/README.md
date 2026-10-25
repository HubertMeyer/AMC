# Laboratorium tokenów Apple Music

Ten projekt jest laboratoryjną, bezsekretną częścią przyszłej integracji AMC z
MusicKit on the Web. Nie jest wdrożoną usługą i nie włącza sesji Apple Music w
AMC Test ani AMC Public.

Usługa wydaje krótkotrwały developer token ES256 wyłącznie dla jawnie
dopuszczonego originu HTTPS. Prywatny klucz Media Services `.p8` jest czytany
tylko z bezwzględnej ścieżki na serwerze. Nie trafia do odpowiedzi, logów,
źródeł ani aplikacji Windows.

## Konfiguracja

- `APPLE_MUSIC_TEAM_ID` — dziesięcioznakowy Team ID;
- `APPLE_MUSIC_KEY_ID` — dziesięcioznakowy identyfikator klucza;
- `APPLE_MUSIC_PRIVATE_KEY_FILE` — bezwzględna ścieżka do prywatnego klucza
  Media Services w formacie PEM/PKCS#8;
- `APPLE_MUSIC_ALLOWED_ORIGINS` — maksymalnie 16 dokładnych originów HTTPS,
  rozdzielonych przecinkami, bez ścieżki;
- `APPLE_MUSIC_TOKEN_LIFETIME_MINUTES` — opcjonalnie 5–1440 minut, domyślnie
  60;
- `APPLE_MUSIC_TRUSTED_PROXIES` — opcjonalna lista dokładnych adresów IP
  reverse proxy, maksymalnie 16.

Endpoint `POST /v1/developer-token` nie przyjmuje ciała i wymaga nagłówka
`Origin` zgodnego z listą. Token zawiera tylko `iss`, `iat`, `exp` i jedno
żądane źródło w claimie `origin`. Limit wynosi 30 wydań na minutę osobno dla
adresu klienta. `/health/live` potwierdza proces, a `/health/ready` potwierdza
kompletną konfigurację bez ujawniania identyfikatorów.

Testy:

```text
dotnet run --project tests/AccessibleMediaController.AppleMusicTokenBroker.SmokeTests/AccessibleMediaController.AppleMusicTokenBroker.SmokeTests.csproj -c Release
```

## Bramka dalszej pracy

Prawdziwa próba wymaga aktywnego zespołu Apple Developer, Media ID, klucza
Media Services i świadomej zgody właściciela zespołu. Klucz znajomego nie staje
się własnością AMC i nie powinien być przesyłany do autora ani wklejany do
czatu. Jeśli posłuży do eksperymentu, właściciel umieszcza go bezpośrednio na
kontrolowanym przez siebie serwerze, a wynik nie jest jeszcze podstawą wydania
publicznego.

Oficjalne źródła:

- https://developer.apple.com/documentation/applemusicapi/generating-developer-tokens
- https://developer.apple.com/documentation/applemusicapi/user-authentication-for-musickit
- https://developer.apple.com/musickit/
- https://developer.apple.com/help/account/capabilities/create-a-media-identifier-and-private-key
