# Hoe lees je met Claude je AI-zichtbaarheid uit Search Console?

Eén prompt en een skill waarmee Claude elke maand twee exports uit Google Search Console doorrekent. Je ziet welke pagina's Google toont in AI Overviews en AI Mode, welke daarvan weinig kliks krijgen, welke zoekopdrachten net buiten pagina 1 staan, wat er steeg of daalde en welke pagina's je deze maand bijwerkt. Claude rekent met code en zet bij elke lijst de regel die besliste. Zo kun je elk getal narekenen.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/search-console-maandcheck

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `prompt.md` | Waar je de twee exports maakt, plus de plak-prompt |
| `skills/search-console-maandcheck/SKILL.md` | Dezelfde werkwijze als skill, zodat je niets meer hoeft te plakken |
| `.claude-plugin/plugin.json` | Zodat je de skill in Claude Code als plugin installeert |

## Zo gebruik je het

**De kortste route.** Maak de twee exports uit `prompt.md`, upload ze in een nieuw gesprek in Claude en plak de prompt eronder. Werkt op elk Claude-plan, ook het gratis plan. Code-uitvoering moet aanstaan bij je instellingen. In ChatGPT werkt dezelfde prompt, in een gesprek waarin je bestanden kunt uploaden.

**Doe je dit elke maand? Gebruik de skill.**

In de Claude-app of op claude.ai:

1. Zet code-uitvoering aan bij je instellingen. Zonder die instelling werken skills niet.
2. Download deze repo als ZIP (knop Code > Download ZIP) en pak hem uit.
3. Maak van de map `diy/search-console-maandcheck/skills/search-console-maandcheck` een ZIP-bestand en upload dat bij Customize, onder Skills.

In Claude Code:

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install search-console-maandcheck@claude-code-toolkit
```

Zelf iets vergelijkbaars maken? De skill-creator van Claude helpt je een eigen skill op te zetten. Zeg bijvoorbeeld: "Maak een skill van deze maandcheck, met mijn eigen grenzen."

## Wat het niet doet

- Kliks uit AI-antwoorden tonen. Google's rapport over generatieve AI telt alleen vertoningen.
- Verder kijken dan de 1.000 rijen die Search Console per tabblad exporteert.
- Voorspellen of een pagina na een update stijgt. Het wijst aan waar je begint.

## Licentie

MIT, net als de rest van deze toolkit.
