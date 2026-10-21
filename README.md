# fris-alcoholmanagement

Een open source webapp voor mensen die hun alcoholgebruik willen bijhouden, minderen of stoppen. Je registreert per dag wat je drinkt (of dat je niets dronk), stelt een doel en ziet op je dashboard hoe het gaat, met tips, mijlpalen en een persoonlijk dagboek.

De app heet **Fris**; de naam is in te stellen met `SITE_NAME`.

> ⚠️ Deze app is een hulpmiddel en vervangt geen medisch advies. Hulp nodig? Kijk op [alcoholinfo.nl](https://www.alcoholinfo.nl) of bel de Trimbos-hulplijn: 0900-1995.

[English summary below](#english)

## Functies

- Dagelijks registreren in standaardglazen (bier, wijn, sterk, enz.), ook alcoholvrije dagen
- Dashboard met trends, statistieken, mijlpalen en gepersonaliseerde tips
- Doelen: maximaal aantal glazen per week, aantal alcoholvrije dagen, of volledig stoppen, met begeleiding per stopfase
- Gemiste dagen achteraf invullen
- Persoonlijk dagboek (rich text, server-side gesanitized)
- Inloggen met gebruikersnaam en wachtwoord of met een **passkey** (WebAuthn)
- Wachtwoord resetten via e-mail (optioneel e-mailadres in profiel)
- Te installeren als **Progressive Web App** op telefoon of desktop
- Publieke landingspagina, privacyverklaring en een one-pager voor partners (`/partners`)

## Snelstart

Vereist: Python 3.10 of nieuwer.

```bash
git clone https://github.com/psinke1974/fris-alcoholmanagement.git
cd fris-alcoholmanagement
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # pas SECRET_KEY aan
python run.py
```

Open [http://localhost:8080](http://localhost:8080). De SQLite-database wordt automatisch aangemaakt in `data/`.

## Testen

```bash
pip install -r requirements-dev.txt
pytest
```

## Productie

Draai de app achter HTTPS met een WSGI-server, bijvoorbeeld:

```bash
gunicorn -w 2 -b 127.0.0.1:8080 "app:create_app()"
```

Zonder een eigen `SECRET_KEY` weigert de app buiten development te starten. Zie [docs/deployment.md](docs/deployment.md) voor alle stappen.

## Documentatie

| Document | Inhoud |
|----------|--------|
| [docs/architecture.md](docs/architecture.md) | Architectuur en mappenstructuur |
| [docs/development.md](docs/development.md) | Lokaal ontwikkelen, testen en conventies |
| [docs/database.md](docs/database.md) | Datamodel en migraties |
| [docs/deployment.md](docs/deployment.md) | In productie draaien |
| [docs/security.md](docs/security.md) | Beveiligingsmaatregelen |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Bijdragen aan het project |
| [SECURITY.md](SECURITY.md) | Een kwetsbaarheid melden |

## Privacy en beveiliging

Alcoholgebruik is gevoelige informatie. Daarom:

- wachtwoorden worden gehasht opgeslagen, passkeys worden ondersteund;
- CSRF-bescherming, een strikte Content-Security-Policy en beveiligingsheaders op elke response;
- alle JavaScript-bibliotheken worden lokaal geserveerd, dus er gaan geen verzoeken naar CDN's of andere derden;
- gegevens zijn per gebruiker geïsoleerd en worden niet gecachet door browser of proxy;
- er is geen tracking en er zijn geen advertenties.

Meer details in [docs/security.md](docs/security.md).

## Licentie

Copyright (C) 2026 Patrick Sinke en bijdragers.

Dit programma is vrije software: je mag het verspreiden en/of aanpassen onder de voorwaarden van de **GNU General Public License versie 3** (of, naar keuze, een latere versie), zoals gepubliceerd door de Free Software Foundation. Het wordt verspreid in de hoop dat het nuttig is, maar ZONDER ENIGE GARANTIE. Zie [LICENSE](LICENSE) voor de volledige tekst.

Meegeleverde bibliotheken van derden (Chart.js, MIT; Quill, BSD-3-Clause) staan in [app/static/vendor](app/static/vendor/README.md) met hun eigen licenties.

---

## English

**fris-alcoholmanagement** is an open source web app (Flask, SQLite) that helps people track, reduce or stop their alcohol use. Users log their daily intake in standard drinks, set a goal (weekly limit, alcohol-free days, or quitting), and get a dashboard with trends, milestones, personalised tips and a private journal. Login works with a password or a passkey (WebAuthn), and the app can be installed as a PWA.

The user interface is in Dutch and follows Dutch guidelines (1 standard drink = 10 g alcohol).

### Quick start

```bash
git clone https://github.com/psinke1974/fris-alcoholmanagement.git
cd fris-alcoholmanagement
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # set SECRET_KEY
python run.py             # http://localhost:8080
```

Run the tests with `pip install -r requirements-dev.txt && pytest`. For production, see [docs/deployment.md](docs/deployment.md) (in Dutch): run behind HTTPS with Gunicorn, set `SECRET_KEY`, `SESSION_COOKIE_SECURE=true` and the WebAuthn domain settings.

### License

Copyright (C) 2026 Patrick Sinke and contributors. Licensed under the [GNU General Public License v3.0 or later](LICENSE). Report security issues as described in [SECURITY.md](SECURITY.md).

This app is a self-help tool and is not a substitute for medical advice.
