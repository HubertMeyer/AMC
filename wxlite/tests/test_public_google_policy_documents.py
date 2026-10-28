"""YT-001: statyczny kontrakt dokumentów Google/YouTube dla AMC Public."""

from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DOCUMENTS = REPOSITORY_ROOT / "docs" / "public"
PRIVACY_POLICY = PUBLIC_DOCUMENTS / "POLITYKA_PRYWATNOSCI_AMC.md"
TERMS = PUBLIC_DOCUMENTS / "WARUNKI_KORZYSTANIA_AMC.md"
READINESS = PUBLIC_DOCUMENTS / "GOTOWOSC_GOOGLE_YOUTUBE.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_privacy_policy_preserves_required_youtube_disclosures() -> None:
    text = _normalized(PRIVACY_POLICY)

    for required in (
        "YouTube API Services",
        "https://www.youtube.com/t/terms",
        "https://policies.google.com/privacy",
        "https://security.google.com/settings/security/permissions",
        "youtube.readonly",
        "ręczna i jednokierunkowa",
        "AMC nie pobiera hasła do konta Google",
        "30 dni",
        "7 dni",
        "Windows",
        "PKCE",
    ):
        assert required in text


def test_drafts_cannot_silently_lose_publication_blockers() -> None:
    privacy = _normalized(PRIVACY_POLICY)
    terms = _normalized(TERMS)
    readiness = _normalized(READINESS)

    assert "nie jest jeszcze przeznaczony do publikacji" in privacy
    assert "nie jest jeszcze przeznaczony do publikacji" in terms
    assert "DO UZUPEŁNIENIA" in privacy
    assert "zamknąć punkty wskazane w liście" in terms
    assert "gotowości Google/YouTube" in terms
    assert "cofa refresh token w oficjalnym punkcie Google" in readiness
    assert "starsze niż 30 dni są usuwane" in readiness
    assert "produkcyjnym klientem Google" in privacy
    assert "czystym profilem użytkownika" in privacy


def test_terms_preserve_youtube_acceptance_and_revocation_links() -> None:
    text = _normalized(TERMS)

    assert "użytkownik zgadza się przestrzegać Warunków korzystania z YouTube" in text
    assert "https://www.youtube.com/t/terms" in text
    assert "https://developers.google.com/youtube/terms/api-services-terms-of-service" in text
    assert "https://security.google.com/settings/security/permissions" in text


def test_readiness_links_only_official_requirement_sources() -> None:
    text = _read(READINESS)

    for required in (
        "https://developers.google.com/youtube/terms/developer-policies",
        "https://developers.google.com/identity/verification/authentication-verification",
        "https://developers.google.com/identity/verification/authentication-policy-compliance",
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "https://uodo.gov.pl/pl/493/4098",
    ):
        assert required in text
