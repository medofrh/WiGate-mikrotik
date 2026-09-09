"""Erzeugt Benutzernamen, Passwörter, MikroTik-Befehle und die CSV-Ausgabe.

Alle Zufallswerte stammen aus ``secrets``.  Das Alphabet enthält bewusst keine
Zeichen, die beim Abtippen verwechselt werden können (0/O/o und 1/l/I/i).
"""

from __future__ import annotations

import csv
import io
import os
import secrets
from dataclasses import dataclass, asdict
from typing import Iterable
from urllib.parse import quote

# 31 Zeichen ohne Verwechslungsgefahr.
ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"
DIGITS = frozenset("23456789")
LETTERS = frozenset(ALPHABET) - DIGITS

PASSWORD_LENGTH = 8
MIN_USERNAME_BODY = 3
MAX_USERNAME_BODY = 8
DEFAULT_PREFIX = "acb-"
BLANK_LABEL = "Blank"

COMMAND_TEMPLATE = (
    '/ip/hotspot/user/add name={username} password="{password}" '
    "server={server} profile={profile}"
)
CSV_HEADER = ["firstname", "lastname", "birthday", "username", "password"]


def username_prefix() -> str:
    """Präfix aller Benutzernamen (per Umgebungsvariable anpassbar)."""
    prefix = os.getenv("USERNAME_PREFIX", DEFAULT_PREFIX).strip()
    return prefix or DEFAULT_PREFIX


@dataclass
class Person:
    firstname: str
    lastname: str
    birthday: str = ""


@dataclass
class GeneratedUser:
    firstname: str
    lastname: str
    birthday: str
    username: str
    password: str
    blank: bool
    qr: str

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def display_name(self) -> str:
        if self.blank:
            return BLANK_LABEL
        return " ".join(part for part in (self.firstname, self.lastname) if part)


def _body_length(total: int) -> int:
    """Wählt die Länge so, dass der Namensraum mindestens 50x größer ist."""
    length = MIN_USERNAME_BODY
    while length < MAX_USERNAME_BODY and len(ALPHABET) ** length < max(total, 1) * 50:
        length += 1
    return length


class UsernameFactory:
    """Liefert garantiert eindeutige Benutzernamen."""

    def __init__(self, total: int, prefix: str | None = None) -> None:
        self.prefix = prefix or username_prefix()
        self.length = _body_length(total)
        self.taken: set[str] = set()

    def next(self) -> str:
        for attempt in range(1, 1001):
            body = "".join(secrets.choice(ALPHABET) for _ in range(self.length))
            candidate = self.prefix + body
            if candidate not in self.taken:
                self.taken.add(candidate)
                return candidate
            # Zu viele Kollisionen: Namensraum vergrößern.
            if attempt % 50 == 0 and self.length < MAX_USERNAME_BODY:
                self.length += 1
        raise RuntimeError("Es konnte kein freier Benutzername erzeugt werden.")


def generate_password(length: int = PASSWORD_LENGTH) -> str:
    """Passwort aus dem eindeutigen Alphabet, mit Buchstabe *und* Ziffer."""
    while True:
        password = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if any(c in DIGITS for c in password) and any(c in LETTERS for c in password):
            return password


def render_login_url(template: str, username: str, password: str) -> str:
    """Setzt Benutzername und Passwort in die QR-Vorlage ein."""
    result = template
    for token, value in (("username", username), ("password", password)):
        encoded = quote(value, safe="")
        result = result.replace("{{" + token + "}}", encoded)
        result = result.replace("{" + token + "}", encoded)
    return result


def build_users(
    people: Iterable[Person],
    extra_users: int,
    qr_template: str,
    prefix: str | None = None,
) -> list[GeneratedUser]:
    people = list(people)
    factory = UsernameFactory(len(people) + extra_users, prefix)
    users: list[GeneratedUser] = []

    def _make(firstname: str, lastname: str, birthday: str, blank: bool) -> GeneratedUser:
        username = factory.next()
        password = generate_password()
        return GeneratedUser(
            firstname=firstname,
            lastname=lastname,
            birthday=birthday,
            username=username,
            password=password,
            blank=blank,
            qr=render_login_url(qr_template, username, password),
        )

    for person in people:
        users.append(_make(person.firstname, person.lastname, person.birthday, False))
    for _ in range(extra_users):
        users.append(_make("", "", "", True))
    return users


def build_commands(users: Iterable[GeneratedUser], server: str, profile: str) -> str:
    lines = [
        COMMAND_TEMPLATE.format(
            username=user.username,
            password=user.password,
            server=server,
            profile=profile,
        )
        for user in users
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def build_csv(users: Iterable[GeneratedUser]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_HEADER)
    for user in users:
        if user.blank:
            writer.writerow([BLANK_LABEL, BLANK_LABEL, BLANK_LABEL, user.username, user.password])
        else:
            writer.writerow(
                [user.firstname, user.lastname, user.birthday, user.username, user.password]
            )
    return buffer.getvalue()
