# Bijdragen

Fijn dat je wilt bijdragen! Issues en pull requests zijn welkom, in het Nederlands of Engels.

## Werkwijze

1. Fork de repository en maak een branch vanaf `main`.
2. Zet een ontwikkelomgeving op (zie [docs/development.md](docs/development.md)).
3. Schrijf of pas tests aan in `tests/` en draai `pytest`.
4. Open een pull request met een korte beschrijving van wat en waarom.

## Richtlijnen

- Houd routes dun; bedrijfslogica hoort in `app/services/`.
- Geen externe scripts of CDN's: nieuwe frontend-bibliotheken gaan in `app/static/vendor/` met hun licentie.
- Geen inline event handlers (`onclick=` e.d.); inline `<script>` krijgt `nonce="{{ csp_nonce }}"`.
- Commit nooit `.env`, databases of andere bestanden met (persoons)gegevens.
- Teksten in de app zijn in het Nederlands.

## Licentie van bijdragen

Door bij te dragen ga je ermee akkoord dat je bijdrage wordt gelicentieerd onder de [GNU General Public License v3.0 of later](LICENSE), dezelfde licentie als de rest van het project.
