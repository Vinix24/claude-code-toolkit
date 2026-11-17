---
name: stem
description: Legt één keer vast hoe de gebruiker schrijft, in linkedin/stem.md, met bij elke regel een citaat uit zijn eigen tekst als bewijs. Zet ook de regels voor de redacteur klaar in .claude/slop-lint.json en maakt linkedin/logboek.csv aan. Gebruik bij "maak mijn stem", "stel de LinkedIn-redactie in", of wanneer /week merkt dat linkedin/stem.md ontbreekt. Onderdeel van de plugin linkedin-redactie.
---

# Stem: hoe jij schrijft, als bestand

Deze skill draait één keer, of opnieuw als de gebruiker vindt dat zijn stem veranderd is. De skills `haken` en `concept` lezen `linkedin/stem.md` bij elke post.

Een stem beschrijf je alleen met wat je in de eigen teksten van de gebruiker ziet. Een stijlgids uit je hoofd is geen stem.

## Stap 1: vragen, in één bericht

Stel deze vragen samen en wacht op het antwoord:

1. Wat doet je bedrijf en voor wie? Eén alinea.
2. Wie wil je met LinkedIn bereiken: welke functie, welke branche?
3. Over welke twee tot vier onderwerpen wil je vaker schrijven? Dat worden je pijlers.
4. Plak vijf tot tien teksten die je zelf schreef: posts, mails of berichten. Onbewerkt en niet met AI gemaakt.
5. Welke woorden of zinnen gebruik je nooit?

Krijg je minder dan vijf teksten, zeg dan dat de stem algemener wordt. Vraag om mails of appjes die de gebruiker zelf schreef. Ga verder vanaf drie teksten.

## Stap 2: linkedin/stem.md

Schrijf het bestand met deze kopjes:

```markdown
# Mijn stem

## Wie ik ben en voor wie ik schrijf
<vraag 1 en 2, in de woorden van de gebruiker>

## Pijlers
- <pijler 1>
- <pijler 2>

## Stemregels
1. <regel> | bewijs: "<citaat van hooguit vijftien woorden>"
2. ...

## Nooit
- <woord of zin uit vraag 5>
```

Regels voor de stemregels:

- Hooguit tien.
- Elke regel krijgt een letterlijk citaat uit de teksten van vraag 4. Een regel zonder citaat schrijf je niet op.
- Kijk naar zinslengte, je of u, woorden die vaak terugkomen, de opening en het slot. Kijk ook of de gebruiker getallen of voorbeelden gebruikt.

Laat het bestand zien. Vraag per regel of hij klopt. Schrap wat de gebruiker niet herkent.

## Stap 3: de regels voor de redacteur

De redacteur gebruikt de plugin `slop-lint`. Controleer of de skill `slop-check` beschikbaar is. Zo niet, geef deze twee regels en zeg dat de redacteur zonder die plugin niet werkt:

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install slop-lint@claude-code-toolkit
```

Lees daarna `${CLAUDE_SKILL_DIR}/slop-lint-sjabloon.json`.

- Vervang bij `eigen-woord` de tekst `VERVANG-DOOR-JOUW-WOORDEN` door de woorden uit vraag 5, gescheiden door `|`. Neem alleen woorden met letters, cijfers, spaties en streepjes over. Een woord met een ander teken laat je weg; noem het aan de gebruiker. Geen woorden opgegeven: laat de regel staan zoals hij is. Hij vindt dan niets.
- Laat `klant-naam` staan zoals hij is.
- Bestaat `.claude/slop-lint.json` nog niet in de projectmap, schrijf het sjabloon daar neer.
- Bestaat hij al, voeg dan alleen de vijf regels toe onder `rules` en de paden toe aan de lijst onder `exclude`. Verander niets anders.

De `exclude`-lijst houdt de automatische controle van slop-lint weg bij bestanden met citaten van klanten en bij het eerste concept. Zo meet de redacteur zelf de eerste ronde.

Zeg daarna letterlijk tegen de gebruiker:

> Open `.claude/slop-lint.json` en vervang `VERVANG-DOOR-KLANTNAMEN` door de namen van je klanten en hun bedrijven, gescheiden door een `|`. Bijvoorbeeld: `Jansen|Bakker Bouw`. Doe dit zelf in het bestand en plak de namen niet in dit gesprek. Dan staan ze niet in de chat en vindt de redacteur ze toch.

Open `.claude/slop-lint.json` daarna zelf niet meer.

## Stap 4: het logboek

Bestaat `linkedin/logboek.csv` nog niet, maak hem aan met alleen deze kopregel:

```
datum,pijler,haak,eerste_regel,vertoningen,interacties
```

## Klaar

Zeg wat er nu staat: `linkedin/stem.md`, `.claude/slop-lint.json` en `linkedin/logboek.csv`. Zeg dat de volgende stap `/linkedin-redactie:week` is, met eerst gespreksnotities in de map van die week.
