# Openbare demo

Met `DEMO_MODE=true` draait Fris als demo-omgeving. Bezoekers klikken op **Probeer de demo** en krijgen direct een tijdelijk account met acht weken voorbeeldgegevens: registraties met een dalende trend, een actief weekdoel, drie dagboekentries en twee niet-ingevulde dagen (om de inhaalmodus te laten zien).

## Wat de demo-modus doet

| Gedrag | Toelichting |
|--------|-------------|
| Geen eigen accounts | `/register` en wachtwoordherstel zijn uitgeschakeld, zodat er geen echte gezondheidsgegevens in de demo belanden |
| Tijdelijke accounts | Elk demo-account heeft `users.demo_expires_at`; na `DEMO_ACCOUNT_TTL_HOURS` (standaard 4) geldt het niet meer als ingelogd en wordt het met alle gegevens verwijderd |
| Opruimen | Verlopen accounts worden bij het opstarten, bij elke nieuwe demo en daarnaast hooguit eens per 5 minuten verwijderd |
| Maximum | Nooit meer dan `DEMO_MAX_ACCOUNTS` (standaard 200) tegelijk; daarboven gaan de oudste eerst weg |
| Rem | Per IP-adres maximaal `DEMO_MAX_PER_IP_PER_HOUR` (standaard 10) nieuwe demo's per uur |
| Banner | Op elke pagina staat dat het een demo is en dat je geen echte gegevens moet invullen |
| Veiligheidsslot | De app weigert te starten in demo-modus als de database gewone (niet-demo) accounts bevat |

Zet `DEMO_MODE` dus **nooit** aan op een installatie met echte gebruikers; gebruik voor de demo altijd een aparte, lege database.

## Lokaal proberen

```bash
DEMO_MODE=true DATABASE_URL=sqlite:////tmp/fris-demo.db python run.py
```

## Online zetten

De repo bevat een `Dockerfile` (Gunicorn, draait niet als root) en een `render.yaml`.

### Render (gratis plan)

1. Log in op [render.com](https://render.com) en kies **New → Blueprint**.
2. Koppel deze GitHub-repo; Render leest `render.yaml` en maakt de service `fris-demo`.
3. Vul bij de vraag om `CONTACT_EMAIL` een contactadres in. `SECRET_KEY` wordt automatisch gegenereerd.
4. Na de build staat de demo op `https://fris-demo.onrender.com`. Kreeg de service een andere naam, pas dan `WEBAUTHN_RP_ID` en `WEBAUTHN_ORIGIN` aan.

Op het gratis plan is de schijf tijdelijk en slaapt de service na 15 minuten zonder bezoek (de eerste pagina laadt dan ongeveer een halve minuut). Voor een demo is dat prima: bij een herstart begint de database leeg.

### Andere hosting

Het image werkt op elke container-hosting (Fly.io, Railway, Scaleway, een eigen VPS met Docker):

```bash
docker build -t fris .
docker run -p 8080:8080 \
  -e DEMO_MODE=true \
  -e SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  -e SESSION_COOKIE_SECURE=true -e TRUSTED_PROXIES=1 \
  -e WEBAUTHN_RP_ID=demo.example.org -e WEBAUTHN_ORIGIN=https://demo.example.org \
  fris
```

Zet er altijd HTTPS voor (de meeste platforms doen dat automatisch).
