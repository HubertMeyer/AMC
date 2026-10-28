"""Czysty model segmentowych dat i godzin edytora harmonogramu.

Model nie zna wx ani automatyzacji UI. Kontrolki dostają z niego wyłącznie
użytkowe polskie etykiety; data, liczby i aktywny segment pozostają osobno.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, replace
from datetime import date, time

from . import i18n


MONTH_NAMES = (
    "styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec",
    "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień",
)
MONTH_NAMES_EN = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
DATE_SEGMENTS = ("day", "month", "year")
TIME_SEGMENTS = ("hour", "minute")


def _wrapped(value: int, delta: int, minimum: int, maximum: int) -> int:
    return minimum + ((value - minimum + delta) % (maximum - minimum + 1))


@dataclass(frozen=True, slots=True)
class DateSegments:
    value: date

    def label(self, segment: str) -> str:
        english = i18n.active_language() == i18n.ENGLISH
        if segment == "day":
            return f"day {self.value.day}" if english else f"dzień {self.value.day}"
        if segment == "month":
            months = MONTH_NAMES_EN if english else MONTH_NAMES
            prefix = "month" if english else "miesiąc"
            return f"{prefix} {months[self.value.month - 1]}"
        if segment == "year":
            return f"year {self.value.year}" if english else f"rok {self.value.year}"
        raise ValueError("Nieznany segment daty")

    def adjust(self, segment: str, delta: int) -> "DateSegments":
        if segment == "day":
            maximum = calendar.monthrange(self.value.year, self.value.month)[1]
            day = _wrapped(self.value.day, delta, 1, maximum)
            return replace(self, value=self.value.replace(day=day))
        if segment == "month":
            month = _wrapped(self.value.month, delta, 1, 12)
            maximum = calendar.monthrange(self.value.year, month)[1]
            return replace(
                self,
                value=self.value.replace(month=month, day=min(self.value.day, maximum)),
            )
        if segment == "year":
            year = max(1900, min(9999, self.value.year + delta))
            maximum = calendar.monthrange(year, self.value.month)[1]
            return replace(
                self,
                value=self.value.replace(year=year, day=min(self.value.day, maximum)),
            )
        raise ValueError("Nieznany segment daty")

    def replace_segment(self, segment: str, number: int) -> "DateSegments":
        if segment == "day":
            maximum = calendar.monthrange(self.value.year, self.value.month)[1]
            if not 1 <= number <= maximum:
                raise ValueError(f"Dzień musi mieścić się od 1 do {maximum}")
            return replace(self, value=self.value.replace(day=number))
        if segment == "month":
            if not 1 <= number <= 12:
                raise ValueError("Miesiąc musi mieścić się od 1 do 12")
            maximum = calendar.monthrange(self.value.year, number)[1]
            return replace(
                self,
                value=self.value.replace(month=number, day=min(self.value.day, maximum)),
            )
        if segment == "year":
            if not 1900 <= number <= 9999:
                raise ValueError("Rok musi mieć cztery cyfry")
            maximum = calendar.monthrange(number, self.value.month)[1]
            return replace(
                self,
                value=self.value.replace(year=number, day=min(self.value.day, maximum)),
            )
        raise ValueError("Nieznany segment daty")

    def may_extend(self, segment: str, prefix: str) -> bool:
        if segment == "year":
            return len(prefix) < 4
        maximum = (
            calendar.monthrange(self.value.year, self.value.month)[1]
            if segment == "day"
            else 12
        )
        return len(prefix) < 2 and any(
            str(candidate).zfill(2).startswith(prefix)
            for candidate in range(1, maximum + 1)
        )


@dataclass(frozen=True, slots=True)
class TimeSegments:
    value: time

    def label(self, segment: str) -> str:
        english = i18n.active_language() == i18n.ENGLISH
        if segment == "hour":
            return f"hour {self.value.hour}" if english else f"godzina {self.value.hour}"
        if segment == "minute":
            return f"minutes {self.value.minute}" if english else f"minuty {self.value.minute}"
        raise ValueError("Nieznany segment czasu")

    def adjust(self, segment: str, delta: int) -> "TimeSegments":
        if segment == "hour":
            return replace(
                self,
                value=self.value.replace(hour=_wrapped(self.value.hour, delta, 0, 23)),
            )
        if segment == "minute":
            return replace(
                self,
                value=self.value.replace(minute=_wrapped(self.value.minute, delta, 0, 59)),
            )
        raise ValueError("Nieznany segment czasu")

    def replace_segment(self, segment: str, number: int) -> "TimeSegments":
        maximum = 23 if segment == "hour" else 59 if segment == "minute" else None
        if maximum is None:
            raise ValueError("Nieznany segment czasu")
        if not 0 <= number <= maximum:
            name = "Godzina" if segment == "hour" else "Minuty"
            raise ValueError(f"{name} muszą mieścić się od 0 do {maximum}")
        return replace(self, value=self.value.replace(**{segment: number}))

    def may_extend(self, segment: str, prefix: str) -> bool:
        maximum = 23 if segment == "hour" else 59 if segment == "minute" else None
        if maximum is None:
            return False
        return len(prefix) < 2 and any(
            str(candidate).zfill(2).startswith(prefix)
            for candidate in range(0, maximum + 1)
        )


def duration_from_fields(hours_text: str, minutes: int) -> int:
    """Puste godziny oznaczaja zero; calkowicie pusta dlugosc jest bledem."""
    stripped = hours_text.strip()
    if stripped and not stripped.isdecimal():
        raise ValueError("Godziny długości muszą być liczbą albo pozostać puste")
    hours = int(stripped) if stripped else 0
    if not 0 <= hours <= 168:
        raise ValueError("Godziny długości muszą mieścić się od 0 do 168")
    if not 0 <= minutes <= 59:
        raise ValueError("Minuty długości muszą mieścić się od 0 do 59")
    total = hours * 60 + minutes
    if total <= 0:
        raise ValueError("Podaj długość nagrania; puste godziny oznaczają zero")
    return total

