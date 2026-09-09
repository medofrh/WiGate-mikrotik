import re

from app.generator import Person, build_users
from app.pdf import PER_PAGE, build_vouchers, pages_needed

TEMPLATE = "http://hotspot.acb/login?username={username}&password={password}"


def _users(csv_count, extra=0):
    people = [Person(f"Vorname{i}", f"Nachname{i}", "01.05.1995") for i in range(csv_count)]
    return build_users(people, extra, TEMPLATE)


def _page_count(data: bytes) -> int:
    counts = [int(match) for match in re.findall(rb"/Count\s+(\d+)", data)]
    assert counts, "Seitenanzahl nicht gefunden"
    return max(counts)


def test_pdf_is_produced():
    data = build_vouchers(_users(2, 1))
    assert data.startswith(b"%PDF")
    assert len(data) > 1000


def test_ten_vouchers_fit_on_one_page():
    assert PER_PAGE == 10
    assert _page_count(build_vouchers(_users(10))) == 1


def test_page_breaks_happen_after_ten_vouchers():
    assert _page_count(build_vouchers(_users(1))) == 1
    assert _page_count(build_vouchers(_users(11))) == 2
    assert _page_count(build_vouchers(_users(23))) == 3


def test_pages_needed_helper():
    assert pages_needed(0) == 1
    assert pages_needed(10) == 1
    assert pages_needed(11) == 2


def test_blank_and_unusual_names_do_not_break_the_layout():
    users = _users(0, 2)
    users += build_users([Person("Ōsamu", "Müller-Lüdenscheidt-Sehrlangername", "01.05.1995")], 0, TEMPLATE)
    data = build_vouchers(users)
    assert data.startswith(b"%PDF")
