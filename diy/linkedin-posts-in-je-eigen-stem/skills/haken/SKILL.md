---
name: haken
description: Haalt letterlijke zinnen van klanten uit gespreksnotities en DM's en maakt daar openingszinnen voor een LinkedIn-post van, elk met het nummer van de klantzin waar hij op rust. Gebruik bij "maak haken", "haken uit mijn notities", of als eerste stap van /week. Onderdeel van de plugin linkedin-redactie.
---

# Haken: openingen in de woorden van je koper

De waarde van deze stap zit in de letterlijke woorden van de klant. Een model maakt van "we krijgen likes en geen telefoontjes" snel "veel ondernemers worstelen met conversie". Dan is de waarde weg. Daarom haal je eerst zinnen op zonder ze te veranderen. Pas daarna schrijf je.

Invoer: `linkedin/week-<JJJJ>-W<WW>/notities.md` en `linkedin/stem.md`.

## Stap 0: is er invoer

Ontbreekt `notities.md` of is hij leeg, zeg dan wat erin moet en stop:

> Zet in `notities.md` je aantekeningen van gesprekken met klanten of prospects, of DM's die je kreeg. Vervang eerst namen, bedrijven, mailadressen, telefoonnummers en bedragen door [klant], [bedrijf] en [bedrag]. Wat de klant letterlijk zei, zet je tussen aanhalingstekens.

Ontbreekt `linkedin/stem.md`, zeg dan dat eerst de skill `stem` moet draaien en stop.

## Stap 1: klantgegevens

Zie je in de notities nog iets dat op een naam, bedrijf, mailadres, telefoonnummer of bedrag van een klant lijkt, stop dan. Noem alleen het regelnummer en vraag de gebruiker het in het bestand zelf te vervangen. Herhaal het gegeven niet in je antwoord.

## Stap 2: letterlijke klantzinnen

- Haal zinnen op die de klant zelf zei of schreef: een klacht, een vraag, een twijfel of een wens.
- Neem ze woord voor woord over. Verbeter geen taalfouten en kort niets in.
- Zinnen van de gebruiker zelf tellen niet mee. Is niet te zien wie iets zei, laat de zin weg.
- Nummer ze K1, K2 enzovoort. Zet het regelnummer uit `notities.md` erachter.
- Hooguit vijftien zinnen.

Vind je er minder dan drie, zeg dan dat de notities vooral samenvattingen zijn. Geef de tip: schrijf in het volgende gesprek letterlijk op wat de klant zegt, tussen aanhalingstekens. Stop.

## Stap 3: openingen

Schrijf per klantzin hooguit twee openingszinnen, hooguit dertig in totaal. Elke opening:

- volgt de stemregels in `stem.md` en gebruikt geen woord uit het kopje "Nooit"
- houdt de woorden van de klant herkenbaar
- staat op één regel van hooguit twintig woorden
- eindigt met het K-nummer tussen haken, bijvoorbeeld `[K3]`
- bevat geen naam, bedrijf of bedrag

Een opening zonder K-nummer schrijf je niet op.

## Stap 4: 01-haken.md

Schrijf het bestand in de map van de week:

```markdown
# Haken, week <JJJJ>-W<WW>

## Klantzinnen
| K | Zin, letterlijk | Regel in notities.md |
|---|---|---|

## Openingen
### <pijler uit stem.md>
1. <opening> [K1]
2. ...

## Gekozen
<leeg, vult de gebruiker of /week in>
```

Deel de openingen in onder de pijlers uit `stem.md`. Past een opening bij geen enkele pijler, zet hem onder "Overig".

## Stap 5: kiezen

Vraag de gebruiker één opening te kiezen en de pijler waar de post onder valt. Hij mag de opening aanpassen. Zet zijn keuze onder "Gekozen": de opening zoals hij hem wil, het K-nummer en de pijler.

Kies nooit zelf. Stop hier.
