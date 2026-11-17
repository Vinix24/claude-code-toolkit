---
name: vrijdag
description: Zegt per pijler of de gebruiker een LinkedIn-onderwerp opschaalt, houdt of schrapt, met een vaste rekenregel op linkedin/logboek.csv. Een script rekent; het model voegt geen eigen advies toe. Gebruik bij "vrijdag", "hoe deden mijn posts", "wat moet ik schrappen" of "welk onderwerp werkt". Onderdeel van de plugin linkedin-redactie.
---

# Vrijdag: een rekensom, geen mening

Welk onderwerp beter loopt, is een rekensom op je eigen cijfers. Daar hoort geen AI bij. Het script `scripts/vrijdag.py` rekent. Jij laat de uitkomst zien en voegt niets toe.

## Stap 1: is er een logboek

Ontbreekt `linkedin/logboek.csv`, zeg dan dat de skill `stem` hem aanmaakt en dat `/week` er na elke post een regel aan toevoegt. Stop.

## Stap 2: ontbrekende cijfers

Het logboek heeft deze kolommen: `datum,pijler,haak,eerste_regel,vertoningen,interacties`. Na elke post blijven `vertoningen` en `interacties` leeg tot de gebruiker ze invult.

Zeg de gebruiker: open op LinkedIn de statistieken van elke post van een week of ouder. Neem het aantal vertoningen en het aantal interacties over in het logboek. De gebruiker doet dat zelf. Jij leest geen LinkedIn-pagina's.

## Stap 3: rekenen

Draai vanuit de projectmap:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/vrijdag.py" linkedin/logboek.csv
```

Exitcode 2 betekent dat het bestand of een kolom niet klopt. Geef de foutmelding door en stop.

Schrijf de uitvoer letterlijk naar `linkedin/vrijdag-<JJJJ-MM-DD>.md` en laat hem zien.

## Stap 4: niets toevoegen

- Reken niets zelf na en geef geen advies dat niet in de uitvoer staat.
- "Te weinig data" van het script is het antwoord. Zoek geen patroon in twee posts.
- Vraagt de gebruiker waarom, leg dan de regel uit die onderaan de uitvoer staat.

Strenger of soepeler rekenen kan met opties:

```
--weken 8      hoe ver terug
--minimum 3    vanaf hoeveel posts per pijler er een advies komt
--rijp 7       posts jonger dan dit aantal dagen tellen niet mee
```
