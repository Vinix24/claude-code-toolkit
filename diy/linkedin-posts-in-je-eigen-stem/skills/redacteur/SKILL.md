---
name: redacteur
description: Laat de linter slop-lint een LinkedIn-concept meten en herschrijft alleen de zinnen die de linter aanwijst. Vindt ook klantgegevens via de eigen regels in .claude/slop-lint.json en legt die voor in plaats van ze zelf te wijzigen. Gebruik bij "redigeer de post", "haal de AI-taal eruit", of als derde stap van /week. Vereist de plugin slop-lint. Onderdeel van de plugin linkedin-redactie.
---

# Redacteur: meten met een lijst, herschrijven met een model

Waarom een linter: een vaste lijst vindt elke keer hetzelfde en zegt welke regel raakte. Een model dat de post nakijkt, kan bij elke ronde iets anders vinden. Daarom meet `slop-lint` en herschrijf jij alleen wat gemeten is.

Invoer: `02-post.md` in de map van de week.

## Stap 0: is de linter er

Is de skill `slop-check` uit de plugin `slop-lint` niet beschikbaar, stop dan en geef:

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install slop-lint@claude-code-toolkit
```

Ga zonder linter niet verder. Controleer de post niet uit je hoofd: dan is het geen meting.

Open `.claude/slop-lint.json` niet. Daar staan de namen van klanten.

## Stap 1: eerste meting

Draai de skill `slop-check` op `02-post.md`, met de optie `--min-woorden 0` zodat een korte post ook gemeten wordt. Gebruik `slop-check` hier alleen om te meten. Het herschrijven doe je volgens stap 2.

Zet de uitvoer letterlijk in `03-redactie.md` onder het kopje "Eerste meting".

## Stap 2: per treffer beslissen

**Regels die met `klant-` beginnen** (`klant-naam`, `klant-mail`, `klant-telefoon`, `klant-bedrag`): wijzig niets. Noem de regel uit de post en vraag de gebruiker wat hij wil: weghalen, vervangen door iets algemeens, of laten staan omdat het geen klantgegeven is. Een bedrag uit eigen werk mag blijven als de gebruiker dat zegt.

**Alle andere regels**: beoordeel of het een echte tic is. Geen tic zijn:

- een opsomming van dingen die even zwaar wegen
- een letterlijke zin van een klant
- de gekozen opening: leg een treffer daarin voor aan de gebruiker en wijzig hem niet zelf

Is het wel een tic, herschrijf dan alleen die zin, in de stem uit `linkedin/stem.md`. Laat elke andere zin staan.

## Stap 3: 03-post.md en de tabel

Schrijf `03-post.md`: de post met alleen de wijzigingen uit stap 2. `02-post.md` blijft staan zoals hij was.

Zet in `03-redactie.md` onder "Wijzigingen":

```markdown
| Regel | Oud | Nieuw of besluit |
|---|---|---|
| komma-en | <oude zin> | <nieuwe zin> |
| drieslag | <zin> | laten staan: opsomming van gelijkwaardige punten |
| klant-bedrag | <zin> | voorgelegd aan de gebruiker |
```

## Stap 4: tweede meting

Draai `slop-check` op `03-post.md` met `--min-woorden 0`. Zet de uitvoer onder "Tweede meting". Staat er nog een tic in die je in stap 2 had moeten herschrijven, herstel hem één keer en meet opnieuw. Daarna stop je, ook als er treffers over zijn: noem ze aan de gebruiker.

## Stap 5: akkoord

Laat `03-post.md` zien, met de tabel en de open vragen over klantgegevens. Vraag om akkoord. Plaats niets.
