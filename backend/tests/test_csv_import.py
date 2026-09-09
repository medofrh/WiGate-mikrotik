from app.csv_import import normalize_date, parse_csv

GOOD = b"firstname,lastname,birthday\nJohn,Doe,01.05.1995\nMaria,Smith,12.08.1998\n"


def test_reads_plain_csv():
    result = parse_csv(GOOD)
    assert result.ok
    assert [person.firstname for person in result.people] == ["John", "Maria"]
    assert result.people[0].birthday == "01.05.1995"


def test_reads_semicolons_and_windows_encoding():
    raw = "firstname;lastname;birthday\nJörg;Müller;01.05.1995\n".encode("cp1252")
    result = parse_csv(raw)
    assert result.ok
    assert result.people[0].lastname == "Müller"


def test_reads_utf8_bom_and_german_headers():
    raw = "Vorname,Nachname,Geburtsdatum\nJohn,Doe,01.05.1995\n".encode("utf-8-sig")
    result = parse_csv(raw)
    assert result.ok
    assert result.people[0].firstname == "John"


def test_normalizes_other_date_formats():
    result = parse_csv(b"firstname,lastname,birthday\nJohn,Doe,1995-05-01\nA,B,1.5.1995\n")
    assert result.ok
    assert [person.birthday for person in result.people] == ["01.05.1995", "01.05.1995"]


def test_missing_lastname_is_reported_with_line_number():
    result = parse_csv(b"firstname,lastname,birthday\nJohn,,01.05.1995\n")
    assert not result.ok
    assert result.errors[0].line == 2
    assert "Nachname" in result.errors[0].message


def test_impossible_date_is_rejected():
    result = parse_csv(b"firstname,lastname,birthday\nJohn,Doe,31.02.1995\n")
    assert not result.ok
    assert "31.02.1995" in result.errors[0].message


def test_unknown_header_gives_clear_error():
    result = parse_csv(b"name,age\nJohn,30\n")
    assert not result.ok
    assert "Kopfzeile" in result.errors[0].message


def test_missing_header_is_accepted_when_rows_look_like_data():
    result = parse_csv(b"John,Doe,01.05.1995\nMaria,Smith,12.08.1998\n")
    assert result.ok
    assert len(result.people) == 2
    assert any("Kopfzeile" in warning.message for warning in result.warnings)


def test_empty_birthday_is_a_warning_only():
    result = parse_csv(b"firstname,lastname,birthday\nJohn,Doe,\n")
    assert result.ok
    assert result.people[0].birthday == ""
    assert result.warnings


def test_extra_columns_are_ignored_once():
    result = parse_csv(b"firstname,lastname,birthday\nJohn,Doe,01.05.1995,x\nA,B,01.05.1995,y\n")
    assert result.ok
    assert len([w for w in result.warnings if "Spalten" in w.message]) == 1


def test_duplicate_person_is_a_warning():
    result = parse_csv(GOOD + b"John,Doe,01.05.1995\n")
    assert result.ok
    assert any("mehrfach" in warning.message for warning in result.warnings)


def test_blank_lines_are_skipped():
    result = parse_csv(b"firstname,lastname,birthday\n\nJohn,Doe,01.05.1995\n\n")
    assert result.ok
    assert len(result.people) == 1


def test_empty_file_is_rejected():
    assert "leer" in parse_csv(b"   \n").errors[0].message


def test_oversized_file_is_rejected():
    assert not parse_csv(b"x" * (2 * 1024 * 1024 + 1)).ok


def test_normalize_date_helper():
    assert normalize_date("12.08.1998") == "12.08.1998"
    assert normalize_date("1998-08-12") == "12.08.1998"
    assert normalize_date("") is None
    assert normalize_date("kein Datum") is None
