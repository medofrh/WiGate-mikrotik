import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

GOOD_CSV = b"firstname,lastname,birthday\nJohn,Doe,01.05.1995\nMaria,Smith,12.08.1998\n"
SETTINGS = {"server": "hotspot1", "profile": "teachers"}


def _upload(raw: bytes, filename: str = "leute.csv"):
    return client.post("/api/csv/parse", files={"file": (filename, io.BytesIO(raw), "text/csv")})


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_parse_endpoint_returns_people():
    body = _upload(GOOD_CSV).json()
    assert body["count"] == 2
    assert body["errors"] == []
    assert body["people"][0]["lastname"] == "Doe"


def test_parse_endpoint_reports_errors_without_failing():
    response = _upload(b"firstname,lastname,birthday\nJohn,,01.05.1995\n")
    assert response.status_code == 200
    assert response.json()["errors"][0]["line"] == 2


def test_generate_returns_users_commands_and_csv():
    people = _upload(GOOD_CSV).json()["people"]
    body = client.post(
        "/api/generate", json={"people": people, "extra_users": 3, **SETTINGS}
    ).json()
    assert body["counts"] == {"imported": 2, "extra": 3, "total": 5}
    assert len(body["users"]) == 5
    assert len(body["commands"].strip().splitlines()) == 5
    assert body["csv"].startswith("firstname,lastname,birthday,username,password")
    assert body["users"][-1]["blank"] is True


def test_generate_accepts_extra_users_only():
    body = client.post("/api/generate", json={"extra_users": 4, **SETTINGS}).json()
    assert body["counts"]["total"] == 4


def test_generate_rejects_invalid_server_name():
    response = client.post("/api/generate", json={"extra_users": 1, "server": "hot spot;drop", "profile": "teachers"})
    assert response.status_code == 400
    assert "Server" in response.json()["message"]


def test_generate_rejects_missing_profile():
    response = client.post("/api/generate", json={"extra_users": 1, "server": "hotspot1"})
    assert response.status_code == 400
    assert "Profil" in response.json()["message"]


def test_generate_rejects_too_many_extra_users():
    response = client.post("/api/generate", json={"extra_users": 9999, **SETTINGS})
    assert response.status_code == 400
    assert "Zusatz-Benutzer" in response.json()["message"]


def test_generate_rejects_empty_request():
    response = client.post("/api/generate", json={"extra_users": 0, **SETTINGS})
    assert response.status_code == 400
    assert "CSV" in response.json()["message"]


def test_generate_rejects_qr_template_without_placeholders():
    response = client.post(
        "/api/generate",
        json={"extra_users": 1, "qr_template": "http://hotspot.acb/login", **SETTINGS},
    )
    assert response.status_code == 400
    assert "Platzhalter" in response.json()["message"]


def test_qr_template_gets_scheme_and_double_braces():
    body = client.post(
        "/api/generate",
        json={
            "extra_users": 1,
            "qr_template": "hotspot.acb/login?username={{username}}&password={{password}}",
            **SETTINGS,
        },
    ).json()
    assert body["users"][0]["qr"].startswith("http://hotspot.acb/login?username=acb-")


def test_pdf_endpoint_returns_pdf():
    users = client.post("/api/generate", json={"extra_users": 2, **SETTINGS}).json()["users"]
    response = client.post("/api/vouchers.pdf", json={"users": users})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "gutscheine.pdf" in response.headers["content-disposition"]


def test_pdf_endpoint_rejects_empty_user_list():
    response = client.post("/api/vouchers.pdf", json={"users": []})
    assert response.status_code == 400
