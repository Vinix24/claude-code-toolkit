---
name: trechter
description: Zegt welke stap tussen een LinkedIn-reactie en een nieuwe klant lekt, met een vaste rekenregel op linkedin/trechter.csv. Gebruik bij "trechter", "waar lekt het" of "weekcijfers".
---

# Trechter: een rekensom, geen mening

Waar het lekt tussen een reactie en een klant, is een rekensom op je eigen tellingen. Daar hoort geen AI bij. Het script `scripts/trechter.py` rekent. Jij laat de uitkomst zien en voegt niets toe.

## Stap 1: is er een logboek

Heeft de gebruiker een logboek geüpload of geplakt, gebruik dat. Zet geplakte regels eerst in een CSV-bestand. Anders zoek je `linkedin/trechter.csv` in de projectmap.

Is er nergens een logboek, maak dan `linkedin/trechter.csv` aan met alleen deze kopregel en stop daarna:

```
week,reageerders,uit_doelgroep,gesprekken,afspraken,klanten
```

Zeg de gebruiker dat hij elke week één regel invult, bijvoorbeeld op vrijdag:

| Kolom | Wat je telt |
|---|---|
| `week` | De week, als `2026-W47` of een datum in die week |
| `reageerders` | Verschillende mensen die deze week een reactie schreven onder je posts. Een like telt niet |
| `uit_doelgroep` | Hoeveel van hen bij je zouden kunnen kopen |
| `gesprekken` | Gesprekken met iemand uit je doelgroep die reageerde en daarna terugschreef op je bericht |
| `afspraken` | Geboekte kennismakingen of belafspraken uit die gesprekken |
| `klanten` | Nieuwe opdrachten uit die afspraken, in de week dat ze getekend zijn |

Alles telt vanaf een reactie onder een post. Berichten die binnenkomen zonder reactie tellen niet mee: anders lijkt de opvolging te lopen terwijl niemand is opgevolgd.

De gebruiker telt zelf, met de meldingen en de berichten op LinkedIn. Een streepje op het moment dat hij op een reactie antwoordt, is makkelijker dan op vrijdag terugtellen. Jij leest geen LinkedIn-pagina's en je gebruikt geen software die LinkedIn uitleest.

## Stap 2: rekenen

Draai het script `scripts/trechter.py` uit de map van deze skill op het logboek. In Claude Code, vanuit de projectmap:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/trechter.py" linkedin/trechter.csv
```

In een chat op claude.ai gebruik je het pad `scripts/trechter.py` in de map van deze skill, met het geüploade logboek. Exitcode 2 betekent dat het bestand of een kolom niet klopt. Geef de foutmelding door en stop.

Laat de uitvoer letterlijk zien. Werk je in een projectmap, schrijf hem dan ook naar `linkedin/trechter-<JJJJ-MM-DD>.md`.

## Stap 3: niets toevoegen

- Reken niets zelf na en geef geen advies dat niet in de uitvoer staat.
- Eén knelpunt tegelijk. Noem geen tweede, ook niet als een stap eronder er slecht uitziet: die is niet beoordeeld.
- "Te weinig data" is het antwoord. Zoek geen patroon in drie gesprekken.
- Vraagt de gebruiker waarom, leg dan de regel uit die onderaan de uitvoer staat.
- Is het knelpunt `opvolging`, wijs dan op de skill `dm` in deze plugin. De actie bij `doelgroep` en bij `klant` staat al in de uitvoer: voeg er niets aan toe.

De grenzen zijn startwaarden, geen benchmark. Aanpassen aan de eigen cijfers kan met opties:

```
--weken 4          hoeveel weken optellen
--reageerders 10   onder dit aantal is het knelpunt zichtbaarheid
--doelgroep 1/2    deel van de reageerders uit je doelgroep
--opvolging 1/5    gesprekken per reageerder uit je doelgroep
--afspraak 1/4     afspraken per gesprek
--klant 1/5        klanten per afspraak
--minimum 5        een stap telt pas mee bij minimaal dit aantal in de stap erboven
--klant-weken 12   over hoeveel weken de stap klant telt
```
