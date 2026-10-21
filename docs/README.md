# Documentatie

Technische documentatie voor **fris-alcoholmanagement** (standaard app-naam: Helder).

| Document | Beschrijving |
|----------|-------------|
| [Architectuur](architecture.md) | Mappenstructuur, lagen en ontwerpkeuzes |
| [Ontwikkeling](development.md) | Lokaal opzetten, testen en conventies |
| [Database](database.md) | Datamodel en migraties |
| [Deployment](deployment.md) | In productie draaien |
| [Beveiliging](security.md) | Beveiligingsmaatregelen en bekende beperkingen |

## Snelstart

```bash
git clone https://github.com/psinke1974/fris-alcoholmanagement.git
cd fris-alcoholmanagement
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python run.py
```

Open [http://localhost:8080](http://localhost:8080).
