# Beveiliging

Overzicht van de maatregelen in de code. Een kwetsbaarheid gevonden? Zie [SECURITY.md](../SECURITY.md).

| Onderwerp | Maatregel | Waar |
|-----------|-----------|------|
| Wachtwoorden | Gehasht met Werkzeug (`scrypt`/`pbkdf2`), minimaal 8 tekens | `app/models/user.py` |
| Passkeys | WebAuthn via de `webauthn`-library; foutdetails worden gelogd, niet aan de client getoond | `app/blueprints/auth/routes.py` |
| Sessies | HTTP-only, `SameSite=Lax`, `Secure` via `SESSION_COOKIE_SECURE`; sessie wordt vernieuwd bij inloggen | `app/config.py` |
| CSRF | Flask-WTF op alle formulieren en JSON-calls; uitloggen alleen via POST | `app/extensions.py` |
| Open redirect | `?next=` accepteert alleen relatieve paden binnen de site | `_safe_next_url` |
| Brute force | Mislukte inlogpogingen per IP + gebruikersnaam worden afgeremd (HTTP 429) | `app/security.py` |
| Wachtwoordreset | Ondertekende token, 1 uur geldig, ongeldig zodra het wachtwoord is gewijzigd (eenmalig bruikbaar). Het antwoord verraadt niet of een e-mailadres bekend is | `app/services/tokens.py` |
| XSS | Jinja2 auto-escaping; dagboek-HTML wordt gesanitized met `bleach` (whitelist van tags) | `app/services/journal_service.py` |
| Content-Security-Policy | Alleen eigen bronnen, inline scripts alleen met per-request nonce, geen inline event handlers, `frame-ancestors 'none'` | `app/security.py` |
| Overige headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS via HTTPS, `Cache-Control: no-store` voor pagina's | `app/security.py` |
| Derden | Geen CDN's: Chart.js en Quill worden lokaal geserveerd | `app/static/vendor/` |
| Gegevensisolatie | Alle queries filteren op `user_id` van de ingelogde gebruiker | routes en services |
| Invoer | Datum-, aantal-, doel- en profielvelden worden gevalideerd; requests max. 1 MB | routes, `MAX_CONTENT_LENGTH` |
| Configuratie | App start niet buiten development zonder eigen `SECRET_KEY` | `app/__init__.py` |
| Eigen gegevens | Gebruikers downloaden al hun gegevens (JSON, en registraties als CSV met bescherming tegen formule-injectie). Wachtwoordhash en passkey-sleutels zitten niet in de export | `app/services/account_service.py` |
| Account verwijderen | Alleen na wachtwoord en bevestiging, met dezelfde rem als inloggen. Verwijdert alle rijen in één transactie en stuurt `Clear-Site-Data` mee zodat de browser lokale kopieën wist | `app/blueprints/main/account.py` |
| Lokale opslag | De service worker bewaart geen pagina's met `Cache-Control: no-store`, dus geen persoonlijke gegevens op het apparaat; offline verschijnt een statische pagina | `app/static/sw.js` |
| Demo-modus | Geen eigen registratie, tijdelijke accounts die automatisch verdwijnen, en de app weigert demo-modus op een database met echte accounts | `app/services/demo_service.py`, [demo.md](demo.md) |

## Bekende beperkingen

- De inlog-rem is in-memory en per proces; zie [deployment.md](deployment.md).
- `style-src` staat `'unsafe-inline'` toe omdat enkele templates en Quill inline styles gebruiken.
