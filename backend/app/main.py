"""FastAPI-Anwendung: API + Auslieferung der gebauten Vue-Oberfläche."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import generator, pdf
from .csv_import import MAX_BYTES, parse_csv
from .generator import Person
from .models import FIELD_LABELS, GenerateRequest, PdfRequest

STATIC_DIR = Path(os.getenv("STATIC_DIR") or Path(__file__).resolve().parent.parent / "static")
INDEX_FILE = STATIC_DIR / "index.html"

GENERIC_ERROR = "Es ist ein unerwarteter Fehler aufgetreten. Bitte erneut versuchen."

app = FastAPI(title="WiGate-microtik", description="MikroTik Hotspot-Benutzer und Gutscheine")


def _message(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"message": message}, status_code=status_code)


def _friendly_validation_message(exc: RequestValidationError) -> str:
    for error in exc.errors():
        raw = str(error.get("msg", ""))
        if raw.startswith("Value error, "):
            return raw[len("Value error, ") :]
        location = [str(part) for part in error.get("loc", []) if part != "body"]
        field = next((part for part in location if not part.isdigit()), "")
        label = FIELD_LABELS.get(field, field or "Eingabe")
        error_type = str(error.get("type", ""))
        if error_type.startswith(("int_", "float_")):
            return f"Bitte für »{label}« eine gültige Zahl eingeben."
        if error_type == "missing":
            return f"Das Feld »{label}« fehlt."
        return f"Die Eingabe im Feld »{label}« ist ungültig."
    return "Die Eingaben sind unvollständig oder ungültig."


@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _message(_friendly_validation_message(exc))


@app.exception_handler(StarletteHTTPException)
async def _http_handler(request: Request, exc: StarletteHTTPException) -> Response:
    detail = exc.detail if isinstance(exc.detail, str) else GENERIC_ERROR
    return _message(detail, exc.status_code)


@app.exception_handler(Exception)
async def _unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
    return _message(GENERIC_ERROR, 500)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/csv/parse")
async def parse_upload(file: UploadFile = File(...)) -> JSONResponse:
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        return _message("Die Datei ist zu groß. Erlaubt sind maximal 2 MB.")

    result = parse_csv(raw)
    return JSONResponse(
        {
            "filename": file.filename or "",
            "count": len(result.people),
            "people": [
                {
                    "firstname": person.firstname,
                    "lastname": person.lastname,
                    "birthday": person.birthday,
                }
                for person in result.people
            ],
            "errors": [issue.as_dict() for issue in result.errors],
            "warnings": [issue.as_dict() for issue in result.warnings],
        }
    )


@app.post("/api/generate")
async def generate(request: GenerateRequest) -> JSONResponse:
    people = [
        Person(firstname=person.firstname, lastname=person.lastname, birthday=person.birthday)
        for person in request.people
    ]
    users = generator.build_users(people, request.extra_users, request.qr_template)
    return JSONResponse(
        {
            "users": [user.as_dict() for user in users],
            "commands": generator.build_commands(users, request.server, request.profile),
            "csv": generator.build_csv(users),
            "counts": {
                "imported": len(people),
                "extra": request.extra_users,
                "total": len(users),
            },
        }
    )


@app.post("/api/vouchers.pdf")
async def vouchers(request: PdfRequest) -> Response:
    users = [
        generator.GeneratedUser(
            firstname=user.firstname,
            lastname=user.lastname,
            birthday=user.birthday,
            username=user.username,
            password=user.password,
            blank=user.blank,
            qr=user.qr,
        )
        for user in request.users
    ]
    return Response(
        content=pdf.build_vouchers(users),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="gutscheine.pdf"'},
    )


@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str) -> Response:
    """Liefert die gebaute Oberfläche; unbekannte Pfade landen auf index.html."""
    if not INDEX_FILE.is_file():
        return _message(
            "Die Oberfläche wurde nicht gefunden. Bitte die Anwendung mit "
            "»docker compose up -d --build« starten.",
            503,
        )
    if full_path:
        candidate = (STATIC_DIR / full_path).resolve()
        root = STATIC_DIR.resolve()
        if candidate.is_file() and (candidate == root or root in candidate.parents):
            return FileResponse(candidate)
    return FileResponse(INDEX_FILE)
