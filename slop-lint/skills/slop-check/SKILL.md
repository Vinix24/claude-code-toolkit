---
name: slop-check
description: Controleert Nederlandse tekst op AI-tics en schrijfslop met een deterministische linter, dus zonder model-oordeel. Vangt em-dashes, buzzwords, AI-openers, kommaketens (", en", ", maar") en retorische frames als "niet X maar Y". Gebruik wanneer de gebruiker vraagt een tekst te checken op slop of AI-tics, "lint deze tekst", "haal de AI-tics eruit", "klinkt dit als AI", of na het schrijven van een langere Nederlandse tekst (blog, mail, offerte, rapport) als er geen slop-lint-hook actief is.
argument-hint: "[bestand of map] [--uit REGEL]"
---

# Slop-check

Een linter die tekst toetst aan vaste patronen. Dezelfde tekst geeft altijd dezelfde
uitslag. Jij beoordeelt daarna welke treffers echte tics zijn.

## 1. Bepaal wat er gecontroleerd wordt

- Bestanden of mappen die de gebruiker noemt.
- Anders het bestand dat je net schreef.
- Staat de tekst alleen in het gesprek, schrijf hem dan eerst naar een tijdelijk
  `.md`-bestand en lint dat.

## 2. Draai de linter

Het script staat in de map van deze skill:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/slop_lint.py" --regels <pad> [<pad> ...]
```

- Exitcode 0 is schoon, 1 betekent treffers, 2 is een gebruiksfout.
- Bestanden onder 40 woorden slaat hij over. Voor een kort fragment: `--min-woorden 0`.
- Eén regel uitzetten voor deze run: `--uit komma-maar`. Meerdere keren mag.

## 3. Beoordeel elke treffer

Niet elke treffer is een tic. Mag blijven staan:

- een opsomming van gelijkwaardige elementen;
- een citaat of andermans tekst;
- een vaste uitdrukking waar de regel per ongeluk op aanslaat.

Zeg per treffer of het een tic is, met de reden in een halve zin.

## 4. Herschrijf alleen de tics

| Treffer | Reparatie |
|---|---|
| `em-dash` | Een punt, een komma of een dubbele punt |
| `komma-en` | Komma weg. Is de eerste helft geen zin, dan een punt |
| Drie of meer komma's in een zin | Opsplitsen in korte zinnen |
| `niet-X-maar-Y`, `geen-X-maar-Y` | Schrijf de Y, laat de X weg |
| `buzzword` | Een getal of een concreet voorbeeld, anders schrappen |
| `ai-opener`, `ai-overgang` | Schrappen en direct de kern in |
| `drieslag` | Kies het element dat klopt, of maak er één zin met een getal van |

Vroeg de gebruiker alleen om een check, toon dan de voorstellen en wijzig niets.

## 5. Meet opnieuw

Draai de linter nog eens op het resultaat en meld de nieuwe uitslag naast de oude.

## Instellen

De gebruiker kan regels uitzetten, eigen regels toevoegen en de woordgrens of een lat
instellen in `.claude/slop-lint.json` in het project, of in `~/.claude/slop-lint.json`
voor alle projecten. De sleutels staan in de README van de plugin. In de tekst zelf zet
`slop-negeer: <reden>` op een regel die treffer uit.

## Zonder Python

Kan je geen code uitvoeren, lees dan de patronen in `scripts/slop_lint.py` (de
woordenboeken `LEXICAAL`, `STRUCTUUR` en `FRAMES`) en pas ze met de hand toe. Meld de
gebruiker dan dat de uitslag niet deterministisch gemeten is.
