import re

from app.generator import (
    ALPHABET,
    BLANK_LABEL,
    Person,
    build_commands,
    build_csv,
    build_users,
    generate_password,
    render_login_url,
)

TEMPLATE = "http://hotspot.acb/login?username={username}&password={password}"
CONFUSING = set("0O1lI")


def _people(count):
    return [Person(f"Vorname{i}", f"Nachname{i}", "01.05.1995") for i in range(count)]


def test_usernames_are_unique_and_prefixed():
    users = build_users(_people(1500), 500, TEMPLATE)
    assert len(users) == 2000
    names = {user.username for user in users}
    assert len(names) == 2000
    assert all(name.startswith("acb-") for name in names)


def test_usernames_and_passwords_avoid_confusing_characters():
    users = build_users(_people(50), 50, TEMPLATE)
    for user in users:
        body = user.username.removeprefix("acb-")
        assert not CONFUSING & set(body + user.password)
        assert set(body + user.password) <= set(ALPHABET)


def test_username_body_is_short():
    users = build_users(_people(10), 0, TEMPLATE)
    assert all(len(user.username) == len("acb-") + 3 for user in users)


def test_password_has_letter_and_digit():
    for _ in range(200):
        password = generate_password()
        assert len(password) == 8
        assert any(char.isdigit() for char in password)
        assert any(char.isalpha() for char in password)


def test_blank_users_are_appended_and_flagged():
    users = build_users(_people(3), 2, TEMPLATE)
    assert [user.blank for user in users] == [False, False, False, True, True]
    assert users[-1].display_name == BLANK_LABEL


def test_command_format_matches_specification():
    users = build_users(_people(1), 0, TEMPLATE)
    line = build_commands(users, "hotspot1", "teachers").strip()
    user = users[0]
    assert line == (
        f'/ip/hotspot/user/add name={user.username} password="{user.password}" '
        "server=hotspot1 profile=teachers"
    )


def test_commands_have_one_line_per_user():
    users = build_users(_people(4), 3, TEMPLATE)
    commands = build_commands(users, "hotspot1", "teachers")
    assert len(commands.strip().splitlines()) == 7


def test_csv_output_marks_blank_users():
    users = build_users(_people(1), 1, TEMPLATE)
    rows = build_csv(users).strip().splitlines()
    assert rows[0] == "firstname,lastname,birthday,username,password"
    assert rows[1].startswith("Vorname0,Nachname0,01.05.1995,acb-")
    assert rows[2].startswith(f"{BLANK_LABEL},{BLANK_LABEL},{BLANK_LABEL},acb-")


def test_csv_escapes_special_characters():
    users = build_users([Person('Anna, "Ann"', "Müller", "01.05.1995")], 0, TEMPLATE)
    assert '"Anna, ""Ann"""' in build_csv(users)


def test_qr_url_supports_both_placeholder_styles():
    assert render_login_url(TEMPLATE, "acb-k7x", "k7mrp4qz") == (
        "http://hotspot.acb/login?username=acb-k7x&password=k7mrp4qz"
    )
    doubled = "http://hotspot.acb/login?username={{username}}&password={{password}}"
    assert render_login_url(doubled, "acb-k7x", "k7mrp4qz").endswith("password=k7mrp4qz")


def test_qr_url_is_built_for_every_user():
    users = build_users(_people(2), 1, TEMPLATE)
    for user in users:
        assert re.fullmatch(
            r"http://hotspot\.acb/login\?username=acb-[a-z0-9]+&password=[a-z0-9]+", user.qr
        )
