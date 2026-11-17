---
description: Draait de LinkedIn-redactie voor deze week. Haken, concept en redactie, met een stop voor jouw akkoord na elke stap.
argument-hint: "[week, bijvoorbeeld 2026-W46]"
---

# /week: de regisseur

Je schrijft zelf niets. Je roept de skills van deze plugin aan in een vaste volgorde. Elke skill schrijft een bestand in de map van de week en de volgende leest dat bestand.

## De map van de week

`linkedin/week-<JJJJ>-W<WW>/`. Gebruik `$ARGUMENTS` als de gebruiker een week opgaf. Anders het ISO-weeknummer van vandaag; in een shell geeft `date +%G-W%V` dat.

## De volgorde

0. **Voorwaarden.** Ontbreekt `linkedin/stem.md`, draai dan de skill `stem` en stop daarna. Ontbreekt de map van de week of `notities.md`, maak de map aan, zeg wat er in `notities.md` hoort en stop.
1. **Skill `haken`.** Schrijft `01-haken.md`. Stop tot de gebruiker een opening en een pijler kiest.
2. **Skill `concept`.** Schrijft `02-post.md` en `02-beeld.md`. Stop tot de gebruiker akkoord geeft.
3. **Skill `redacteur`.** Schrijft `03-redactie.md` en `03-post.md`. Stop tot de gebruiker akkoord geeft.
4. **Logboek.** Voeg na het laatste akkoord één regel toe aan `linkedin/logboek.csv`:
   - `datum`: vandaag, als JJJJ-MM-DD
   - `pijler` en `haak`: uit "Gekozen" in `01-haken.md`
   - `eerste_regel`: de eerste regel van `03-post.md`, tussen dubbele aanhalingstekens. Een dubbel aanhalingsteken in die regel schrijf je dubbel
   - `vertoningen` en `interacties`: leeg

   Zeg dan: "Je post staat in `03-post.md`. Plaats hem zelf. Vul over een week de vertoningen en interacties in het logboek in. Op vrijdag rekent de skill `vrijdag` ermee."

## Regels

- Sla geen stap over en voeg er geen toe.
- Een vraag die een skill aan de gebruiker stelt, beantwoord je niet zelf.
- Bestanden van eerdere stappen blijven staan. Een wijziging in een stap komt in het bestand van die stap.
- Plaats nooit iets op LinkedIn. Deze plugin heeft geen koppeling met LinkedIn en je maakt er geen.
