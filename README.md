# WiGate-microtik

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vuedotjs&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-44%20passing-3fb950?logo=pytest&logoColor=white)

MikroTik Hotspot-Benutzer und druckfertige Gutscheine aus einer CSV-Datei erstellen.

**CSV hochladen → Server und Profil eintragen → Zusatz-Benutzer wählen → Vorschau → erzeugen.**

Heraus kommen eine Benutzer-CSV, ein Gutschein-PDF mit QR-Codes und die fertige
MikroTik-Befehlsliste zum Kopieren oder Herunterladen.

---

## Voraussetzungen

Nur **Docker** – sonst nichts. Kein Python, kein Node.js, keine Datenbank.

Prüfen, ob Docker läuft:

```bash
docker --version
docker compose version
```

## Starten

Im Projektordner (dort, wo die `docker-compose.yml` liegt):

```bash
docker compose up -d
```

Beim ersten Mal dauert das ein bis zwei Minuten, weil das Image gebaut wird.
Danach im Browser öffnen:

```
http://localhost:8080
```

Läuft die Anwendung auf einem Server im Netzwerk, stattdessen dessen Adresse
verwenden, zum Beispiel `http://192.168.1.50:8080`.

## Alle Befehle im Überblick

Alle Befehle werden im Projektordner ausgeführt.

| Zweck | Befehl |
| --- | --- |
| Starten (im Hintergrund) | `docker compose up -d` |
| Status anzeigen | `docker compose ps` |
| Logs ansehen (mit `Strg+C` beenden) | `docker compose logs -f` |
| Neu starten | `docker compose restart` |
| Stoppen (Container bleibt bestehen) | `docker compose stop` |
| Stoppen und aufräumen | `docker compose down` |
| Nach Code-Änderungen neu bauen | `docker compose up -d --build` |
| Tests ausführen | `docker build --target test .` |
| Image löschen (alles zurücksetzen) | `docker compose down --rmi local` |

Kopierfertig:

```bash
# starten
docker compose up -d

# nachsehen, ob alles läuft
docker compose ps

# Logs anschauen
docker compose logs -f

# stoppen
docker compose down

# nach Änderungen neu bauen und starten
docker compose up -d --build
```

## Anderen Port verwenden

Standard ist Port **8080**. Einmalig anders starten:

```bash
PORT=9090 docker compose up -d
```

Dauerhaft: eine Datei `.env` neben der `docker-compose.yml` anlegen:

```env
PORT=8080              # Port im Browser
USERNAME_PREFIX=acb-   # Präfix aller Benutzernamen
TZ=Europe/Berlin       # Zeitzone
```

Danach `docker compose up -d` erneut ausführen.

## CSV-Datei

Erste Zeile ist die Kopfzeile, danach eine Zeile je Person
(Beispieldatei: `beispiel.csv`):

```csv
firstname,lastname,birthday
John,Doe,01.05.1995
Maria,Smith,12.08.1998
```

Die Anwendung ist tolerant und erkennt automatisch:

* Trennzeichen `,` `;` und Tabulator (deutsches Excel schreibt `;`)
* die Kodierungen UTF-8 (auch mit BOM) und Windows-1252 (Umlaute)
* die Datumsformate `01.05.1995`, `1.5.1995`, `1995-05-01` und `01/05/1995`
* deutsche Spaltennamen (`Vorname`, `Nachname`, `Geburtsdatum`)

Fehlerhafte Zeilen werden **mit Zeilennummer** gemeldet, statt die ganze Datei
abzulehnen. Ein fehlendes Geburtsdatum ist nur ein Hinweis, kein Fehler.

## Was erzeugt wird

| Datei | Inhalt |
| --- | --- |
| `benutzer.csv` | `firstname,lastname,birthday,username,password` |
| `gutscheine.pdf` | 10 Gutscheine je A4-Seite, mit Schnittlinien und QR-Code |
| `mikrotik-befehle.txt` | eine `/ip/hotspot/user/add`-Zeile je Benutzer |

Eine erzeugte Befehlszeile sieht so aus:

```
/ip/hotspot/user/add name=acb-k7x password="k7mrp4qz" server=hotspot1 profile=teachers
```

Benutzernamen beginnen immer mit `acb-` und sind kurz (z. B. `acb-k7x`).
Benutzernamen und Passwörter verwenden nur Zeichen, die sich beim Abtippen nicht
verwechseln lassen – kein `0`/`O` und kein `1`/`l`/`I`.

**Zusatz-Benutzer** sind Zugänge ohne Namen für kurzfristige Teilnehmer. Sie
erscheinen als `Blank` in CSV und Gutschein.

Der QR-Code enthält den Hotspot-Login-Link, standardmäßig:

```
http://hotspot.acb/login?username={username}&password={password}
```

Der Link ist in der Oberfläche änderbar; `{username}` und `{password}` werden je
Benutzer ersetzt. Server, Profil, Anzahl der Zusatz-Benutzer und der QR-Link
werden im Browser gemerkt.

## Auf einen anderen Rechner umziehen

```bash
# 1. Ordner auf den neuen Rechner kopieren, dann dort:
cd wigate-microtik
docker compose up -d
```

Mehr ist nicht nötig. Es gibt keine Datenbank und keine Konfiguration im Code:
Alles läuft in einem Container, der Oberfläche und API unter demselben Port
ausliefert.

Nichts wird dauerhaft gespeichert. Die erzeugten Passwörter existieren nur, bis
die Seite neu geladen wird – die Dateien deshalb direkt herunterladen.

## Entwicklung

```bash
# Tests ausführen (44 Tests, laufen im Docker-Build)
docker build --target test .

# API lokal mit automatischem Neuladen
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload          # http://localhost:8000

# Oberfläche lokal mit automatischem Neuladen
cd frontend
npm install
npm run dev                            # http://localhost:5173
```

Aufbau: `backend/` (FastAPI, Python 3.12) und `frontend/` (Vue 3, Vite,
Tailwind CSS). Beim Docker-Build wird die Oberfläche gebaut und anschließend von
FastAPI als statische Dateien ausgeliefert.

## Hilfe bei Problemen

| Problem | Lösung |
| --- | --- |
| Seite lädt nicht | `docker compose ps` – Status muss `Up (healthy)` sein |
| Port 8080 belegt | `PORT=9090 docker compose up -d` |
| Änderungen wirken nicht | `docker compose up -d --build` |
| Fehlermeldung unklar | `docker compose logs -f` |
| Ganz von vorne | `docker compose down --rmi local && docker compose up -d` |

---

## Quick start (English)

Requires Docker only:

```bash
docker compose up -d          # start
                              # then open http://localhost:8080
docker compose logs -f        # view logs
docker compose down           # stop and clean up
docker compose up -d --build  # rebuild after changes
docker build --target test .  # run the test suite
```

Upload a CSV (`firstname,lastname,birthday`), enter the MikroTik server and
profile, choose how many spare accounts to add, preview, and generate. You get a
users CSV, a printable voucher PDF with login QR codes, and the ready-to-paste
`/ip/hotspot/user/add` command list. The interface is in German.
