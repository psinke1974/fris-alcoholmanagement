# Ontwikkeling

## Vereisten

- Python 3.10+
- Moderne browser (voor passkeys)

## Opzetten

```bash
git clone https://github.com/psinke1974/fris-alcoholmanagement.git
cd fris-alcoholmanagement
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

Pas `SECRET_KEY` aan in `.env` (gebruik een lange willekeurige string). Met `FLASK_DEBUG=1` (standaard in `.env.example`) draait de app in debug-modus; dan is een eigen `SECRET_KEY` nog niet verplicht.

## Starten

```bash
source .venv/bin/activate
python run.py
```

De app draait op [http://localhost:8080](http://localhost:8080).

## Testen

```bash
source .venv/bin/activate
pytest
```

Tests gebruiken een in-memory SQLite-database (`TestConfig` in `tests/conftest.py`).

## Codeconventies

### Imports

Gebruik altijd het `app`-package:

```python
from app.models import User, DrinkLog
from app.services import compute_stats
```

### Nieuwe route toevoegen

1. Voeg de route toe in het juiste blueprint (`app/blueprints/auth/` of `app/blueprints/main/`)
2. Maak een template in `app/templates/` indien nodig
3. Schrijf een test in `tests/`

### Bedrijfslogica

Plaats logica in `app/services/`, niet in routes of models.

- **stats_service.py** — berekeningen op logdata
- **tips_service.py** — gepersonaliseerde adviezen

### Constanten

Vaste waarden (formulieropties, validatielimieten) horen in `app/constants.py`.

### Database wijzigen

1. Pas het SQLAlchemy-model aan in `app/models/`
2. Maak een migratiescript in `migrations/` (bijv. `002_add_column.sql`)
3. Documenteer de wijziging in `docs/database.md`

## Omgevingsvariabelen

| Variabele | Default | Beschrijving |
|-----------|---------|-------------|
| `SECRET_KEY` | (dev-waarde) | Flask sessiesleutel — **verplicht buiten debug-modus** |
| `FLASK_DEBUG` | `1` via `run.py` | Debug-modus en reloader; nooit in productie |
| `HOST`, `PORT` | `127.0.0.1`, `8080` | Adres van de development-server (`run.py`) |
| `DATABASE_URL` | SQLite in `data/` | SQLAlchemy database-URL |
| `SITE_NAME` | `Helder` | Productnaam in UI, e-mails en PWA |
| `SITE_TAGLINE` | (standaardtekst) | Ondertitel / meta-description |
| `CONTACT_EMAIL` | `contact@example.org` | Contactadres in privacyverklaring en footer |
| `WEBAUTHN_RP_ID` | `localhost` | Relying party ID voor passkeys |
| `WEBAUTHN_RP_NAME` | `SITE_NAME` | Naam getoond bij passkey-registratie |
| `WEBAUTHN_ORIGIN` | `http://localhost:8080` | Origin URL voor WebAuthn |
| `SESSION_COOKIE_SECURE` | `false` | Cookies alleen via HTTPS (`true` in productie) |
| `TRUSTED_PROXIES` | `0` | Aantal reverse proxies voor `X-Forwarded-*` |
| `LOGIN_MAX_ATTEMPTS`, `LOGIN_WINDOW_SECONDS` | `10`, `900` | Rem op mislukte inlogpogingen |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`, `MAIL_USE_TLS` | — | SMTP voor resetmails; zonder `MAIL_SERVER` worden mails gelogd |

## Passkeys in productie

1. Zet `WEBAUTHN_RP_ID` op je domein (zonder `https://`)
2. Zet `WEBAUTHN_ORIGIN` op `https://jouwdomein.nl`
3. Gebruik HTTPS (verplicht voor WebAuthn)

## Frontend en Content-Security-Policy

De app stuurt een strikte CSP mee (zie [security.md](security.md)). Daardoor:

- krijgt elk inline `<script>` het attribuut `nonce="{{ csp_nonce }}"`;
- zijn inline event handlers (`onclick=` e.d.) niet toegestaan; gebruik `data-confirm="…"` of een listener in `app/static/js/`;
- worden externe bibliotheken lokaal opgeslagen in `app/static/vendor/` in plaats van via een CDN geladen.

## Productie

Zie [deployment.md](deployment.md).
