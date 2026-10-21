# In productie draaien

Deze handleiding beschrijft een eenvoudige installatie op één Linux-server met een reverse proxy (nginx of Caddy) voor HTTPS.

## 1. Installeren

```bash
git clone https://github.com/psinke1974/fris-alcoholmanagement.git
cd fris-alcoholmanagement
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn
cp .env.example .env
```

## 2. Configureren (`.env`)

| Variabele | Waarde in productie |
|-----------|---------------------|
| `SECRET_KEY` | **Verplicht.** Genereer met `python -c "import secrets; print(secrets.token_hex(32))"`. Zonder eigen waarde start de app niet. |
| `FLASK_DEBUG` | Weglaten of `0`. Nooit `1` in productie. |
| `SESSION_COOKIE_SECURE` | `true` (cookies alleen via HTTPS) |
| `TRUSTED_PROXIES` | `1` als er één reverse proxy voor de app staat |
| `WEBAUTHN_RP_ID` | Je domein zonder schema, bijv. `fris.example.org` |
| `WEBAUTHN_ORIGIN` | `https://fris.example.org` |
| `SITE_NAME`, `CONTACT_EMAIL` | Naam en contactadres die in de app en privacyverklaring verschijnen |
| `MAIL_*` | SMTP-gegevens voor wachtwoordreset-mails |
| `DATABASE_URL` | Optioneel, standaard SQLite in `data/` |

Zorg dat `.env` en `data/` alleen leesbaar zijn voor de gebruiker die de app draait (`chmod 600 .env`, `chmod 700 data`).

## 3. Starten

```bash
gunicorn -w 2 -b 127.0.0.1:8080 "app:create_app()"
```

Laat Gunicorn alleen op `127.0.0.1` luisteren; de reverse proxy regelt HTTPS. Voorbeeld voor Caddy:

```
fris.example.org {
    reverse_proxy 127.0.0.1:8080
}
```

Gebruik bij voorkeur een systemd-service zodat de app automatisch herstart.

## 4. Aandachtspunten

- **Inlog-rem**: het aantal mislukte inlogpogingen wordt per proces in het geheugen bijgehouden. Bij meerdere workers of servers is de limiet dus per worker. Voor grotere installaties is rate limiting in de reverse proxy aan te raden.
- **Back-ups**: maak regelmatig een versleutelde back-up van de database (`data/minder_drinken.db`). Die bevat gevoelige gezondheidsgerelateerde gegevens.
- **AVG**: alcoholgebruik is een gevoelig persoonsgegeven. Pas de privacyverklaring (`app/templates/privacy.html`) aan op jouw organisatie en verwerking voordat je de app openstelt.
- **Updates**: houd de afhankelijkheden in `requirements.txt` actueel (`pip list --outdated`).
