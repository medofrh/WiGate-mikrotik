"""Toleranter CSV-Import mit verständlichen deutschen Meldungen.

Der Import repariert selbstständig, was sicher reparierbar ist (Kodierung,
Trennzeichen, Datumsformat) und meldet alles andere mit Zeilennummer.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime

from .generator import Person

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000
MAX_NAME_LENGTH = 100
MAX_ISSUES = 50

DATE_FORMATS = (
    "%d.%m.%Y",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d.%m.%y",
)
OUTPUT_DATE_FORMAT = "%d.%m.%Y"
DELIMITERS = (",", ";", "\t", "|")


def _norm(value: str) -> str:
    cleaned = value.strip().strip('"').strip("'").lower()
    for char in ("_", "-", "."):
        cleaned = cleaned.replace(char, " ")
    return " ".join(cleaned.split())


FIRST_ALIASES = {_norm(v) for v in ("firstname", "first name", "vorname", "given name")}
LAST_ALIASES = {_norm(v) for v in ("lastname", "last name", "nachname", "surname", "familienname")}
BIRTH_ALIASES = {
    _norm(v)
    for v in (
        "birthday",
        "birthdate",
        "birth date",
        "date of birth",
        "dob",
        "geburtstag",
        "geburtsdatum",
        "geburt",
    )
}


@dataclass
class Issue:
    message: str
    line: int | None = None

    def as_dict(self) -> dict:
        return {"line": self.line, "message": self.message}


@dataclass
class ParseResult:
    people: list[Person] = field(default_factory=list)
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _add(issues: list[Issue], message: str, line: int | None = None) -> None:
    """Fuegt eine Meldung hinzu und deckelt die Gesamtmenge."""
    if len(issues) < MAX_ISSUES:
        issues.append(Issue(message, line))
    elif len(issues) == MAX_ISSUES:
        issues.append(Issue("Weitere Meldungen wurden ausgeblendet.", None))


def _decode(raw: bytes, warnings: list[Issue]) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    _add(
        warnings,
        "Die Zeichenkodierung wurde nicht erkannt. Einzelne Sonderzeichen "
        "können falsch dargestellt werden.",
    )
    return raw.decode("latin-1", errors="replace")


def _detect_delimiter(text: str) -> str:
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    counts = {delimiter: first_line.count(delimiter) for delimiter in DELIMITERS}
    best = max(counts, key=lambda delimiter: counts[delimiter])
    return best if counts[best] else ","


def normalize_date(value: str) -> str | None:
    """Wandelt gängige Datumsformate in TT.MM.JJJJ um; None wenn ungültig."""
    text = value.strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime(OUTPUT_DATE_FORMAT)
        except ValueError:
            continue
    return None


def _match_header(row: list[str]) -> dict[str, int] | None:
    mapping: dict[str, int] = {}
    for index, cell in enumerate(row):
        name = _norm(cell)
        if name in FIRST_ALIASES and "firstname" not in mapping:
            mapping["firstname"] = index
        elif name in LAST_ALIASES and "lastname" not in mapping:
            mapping["lastname"] = index
        elif name in BIRTH_ALIASES and "birthday" not in mapping:
            mapping["birthday"] = index
    if "firstname" in mapping and "lastname" in mapping:
        return mapping
    return None


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def parse_csv(raw: bytes) -> ParseResult:
    result = ParseResult()

    if len(raw) > MAX_BYTES:
        _add(result.errors, "Die Datei ist zu groß. Erlaubt sind maximal 2 MB.")
        return result

    text = _decode(raw, result.warnings)
    if not text.strip():
        _add(result.errors, "Die Datei ist leer.")
        return result

    delimiter = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    mapping: dict[str, int] | None = None
    expected_columns = 0
    extra_column_reported = False
    seen: set[tuple[str, str, str]] = set()

    for row in reader:
        line = reader.line_num
        if not any(cell.strip() for cell in row):
            continue

        if mapping is None:
            mapping = _match_header(row)
            if mapping is not None:
                if "birthday" not in mapping:
                    _add(
                        result.warnings,
                        "Die Spalte »birthday« fehlt. Die Geburtstage bleiben leer.",
                        line,
                    )
                expected_columns = max(mapping.values()) + 1
                continue
            # Keine Kopfzeile: nur uebernehmen, wenn die Zeile wie Daten aussieht.
            if len(row) >= 3 and normalize_date(row[2]):
                mapping = {"firstname": 0, "lastname": 1, "birthday": 2}
                expected_columns = 3
                _add(
                    result.warnings,
                    "Es wurde keine Kopfzeile gefunden. Die erste Zeile wird als Person gelesen.",
                    line,
                )
            else:
                _add(
                    result.errors,
                    "Die Kopfzeile wurde nicht erkannt. Die erste Zeile muss lauten: "
                    "firstname,lastname,birthday",
                    line,
                )
                return result

        if len(result.people) >= MAX_ROWS:
            _add(
                result.errors,
                f"Die Datei enthält mehr als {MAX_ROWS} Zeilen. Bitte in kleinere "
                "Dateien aufteilen.",
                line,
            )
            break

        if len(row) > expected_columns and not extra_column_reported:
            extra_column_reported = True
            _add(result.warnings, "Zusätzliche Spalten wurden ignoriert.", line)

        firstname = _cell(row, mapping.get("firstname"))[:MAX_NAME_LENGTH]
        lastname = _cell(row, mapping.get("lastname"))[:MAX_NAME_LENGTH]
        raw_birthday = _cell(row, mapping.get("birthday"))

        if not firstname and not lastname:
            _add(result.errors, "Vorname und Nachname fehlen.", line)
            continue
        if not firstname:
            _add(result.errors, "Der Vorname fehlt.", line)
            continue
        if not lastname:
            _add(result.errors, "Der Nachname fehlt.", line)
            continue

        birthday = ""
        if raw_birthday:
            normalized = normalize_date(raw_birthday)
            if normalized is None:
                _add(
                    result.errors,
                    f"»{raw_birthday}« ist kein gültiges Geburtsdatum. "
                    "Erwartet wird das Format TT.MM.JJJJ.",
                    line,
                )
                continue
            birthday = normalized
        elif "birthday" in mapping:
            _add(result.warnings, "Kein Geburtsdatum angegeben.", line)

        key = (firstname.lower(), lastname.lower(), birthday)
        if key in seen:
            _add(result.warnings, f"»{firstname} {lastname}« kommt mehrfach vor.", line)
        seen.add(key)

        result.people.append(Person(firstname=firstname, lastname=lastname, birthday=birthday))

    if mapping is None:
        _add(result.errors, "Die Datei enthält keine Daten.")
    elif not result.people and not result.errors:
        _add(result.errors, "Die Datei enthält keine Personen.")

    return result
