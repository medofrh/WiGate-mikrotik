"""Pydantic-Modelle inklusive Validierung der Benutzereingaben."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_TOTAL_USERS = 2000
MAX_EXTRA_USERS = 500
MAX_TEMPLATE_LENGTH = 500

# MikroTik-Namen: bewusst eng gefasst. Das verhindert nebenbei, dass etwas in
# die erzeugte Befehlsliste eingeschleust werden kann.
NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
SCHEME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")

DEFAULT_QR_TEMPLATE = "http://hotspot.acb/login?username={username}&password={password}"

FIELD_LABELS = {
    "server": "Server",
    "profile": "Profil",
    "extra_users": "Zusatz-Benutzer",
    "qr_template": "QR-Link",
    "people": "Personen",
    "users": "Benutzer",
    "firstname": "Vorname",
    "lastname": "Nachname",
    "birthday": "Geburtsdatum",
}


def normalize_qr_template(value: str) -> str:
    """Prüft die QR-Vorlage und ergänzt fehlendes http://."""
    template = (value or "").strip()
    if not template:
        return DEFAULT_QR_TEMPLATE
    if len(template) > MAX_TEMPLATE_LENGTH:
        raise ValueError(
            f"Der QR-Link ist zu lang (maximal {MAX_TEMPLATE_LENGTH} Zeichen)."
        )
    # {{username}} und {username} sind beide erlaubt.
    normalized = template.replace("{{", "{").replace("}}", "}")
    missing = [
        placeholder
        for placeholder in ("{username}", "{password}")
        if placeholder not in normalized
    ]
    if missing:
        raise ValueError(
            "Der QR-Link muss die Platzhalter {username} und {password} enthalten."
        )
    if not SCHEME_PATTERN.match(normalized):
        normalized = "http://" + normalized
    return normalized


class PersonIn(BaseModel):
    firstname: str = ""
    lastname: str = ""
    birthday: str = ""

    @field_validator("firstname", "lastname", "birthday", mode="before")
    @classmethod
    def _clean(cls, value: object) -> str:
        return str(value or "").strip()[:100]

    @model_validator(mode="after")
    def _require_name(self) -> "PersonIn":
        if not self.firstname and not self.lastname:
            raise ValueError("Eine Person ohne Vor- und Nachnamen kann nicht angelegt werden.")
        return self


class UserIn(BaseModel):
    firstname: str = ""
    lastname: str = ""
    birthday: str = ""
    username: str = ""
    password: str = ""
    blank: bool = False
    qr: str = ""

    @field_validator("firstname", "lastname", "birthday", "username", "password", mode="before")
    @classmethod
    def _clean(cls, value: object) -> str:
        return str(value or "").strip()[:200]

    @field_validator("qr", mode="before")
    @classmethod
    def _clean_qr(cls, value: object) -> str:
        return str(value or "").strip()[:MAX_TEMPLATE_LENGTH]


class GenerateRequest(BaseModel):
    # Ohne validate_default würde Pydantic weggelassene Felder ungeprüft
    # übernehmen – ein fehlendes Profil käme dann leer im Befehl an.
    model_config = ConfigDict(validate_default=True)

    people: list[PersonIn] = Field(default_factory=list)
    extra_users: int = 0
    server: str = ""
    profile: str = ""
    qr_template: str = DEFAULT_QR_TEMPLATE

    @field_validator("server", "profile")
    @classmethod
    def _check_name(cls, value: str, info) -> str:
        label = FIELD_LABELS.get(info.field_name, info.field_name)
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError(f"Das Feld »{label}« darf nicht leer sein.")
        if not NAME_PATTERN.match(cleaned):
            raise ValueError(
                f"Der {label}-Name darf nur Buchstaben, Zahlen, Punkt, Bindestrich "
                "und Unterstrich enthalten (maximal 64 Zeichen)."
            )
        return cleaned

    @field_validator("extra_users")
    @classmethod
    def _check_extra(cls, value: int) -> int:
        if value < 0 or value > MAX_EXTRA_USERS:
            raise ValueError(
                f"Die Anzahl der Zusatz-Benutzer muss zwischen 0 und {MAX_EXTRA_USERS} liegen."
            )
        return value

    @field_validator("qr_template")
    @classmethod
    def _check_template(cls, value: str) -> str:
        return normalize_qr_template(value)

    @model_validator(mode="after")
    def _check_total(self) -> "GenerateRequest":
        total = len(self.people) + self.extra_users
        if total < 1:
            raise ValueError(
                "Es wurden keine Benutzer angefordert. Bitte eine CSV-Datei hochladen "
                "oder Zusatz-Benutzer eintragen."
            )
        if total > MAX_TOTAL_USERS:
            raise ValueError(
                f"Es können maximal {MAX_TOTAL_USERS} Benutzer auf einmal erzeugt werden."
            )
        return self


class PdfRequest(BaseModel):
    users: list[UserIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_users(self) -> "PdfRequest":
        if not self.users:
            raise ValueError("Es wurden keine Benutzer übergeben.")
        if len(self.users) > MAX_TOTAL_USERS:
            raise ValueError(
                f"Es können maximal {MAX_TOTAL_USERS} Gutscheine auf einmal erzeugt werden."
            )
        return self
