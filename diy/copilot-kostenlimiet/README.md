# Hoe zet je een limiet op Copilot die ook echt begrenst?

Microsoft rekent extra Copilot-functies in Copilot Business per gebruik af, bovenop de licentie. Hier vind je een checklist om de instellingen in het Microsoft 365-beheercentrum zelf na te lopen, zonder AI. Daarnaast een plak-prompt die uit jouw teams en jouw budget uitrekent welke limieten je zet. De prompt houdt rekening met de valkuil die de meeste lijstjes missen: bij overlap geldt de ruimste regel.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/copilot-kostenlimiet

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `checklist.md` | De controles in het beheercentrum, om af te vinken, met de bron per feit |
| `prompt.md` | De plak-prompt. Hij vraagt eerst naar je situatie en rekent dan je limieten per team uit |

## Zo gebruik je het

1. Loop `checklist.md` na in het Microsoft 365-beheercentrum, onder **Copilot > Cost management**. Daar is geen AI voor nodig.
2. Plak het codeblok uit `prompt.md` in ChatGPT, Claude of Copilot Chat. Beantwoord de vijf vragen. Zet de limieten uit het antwoord in het beheercentrum.
3. Kijk elke maand vijf minuten bij **Consumption**, weergave **Users**.

De feiten zijn nagekeken op 12 november 2026. Verandert Microsoft iets, pas dan de regel in het feitenblok van de prompt aan en zet de nieuwe datum erboven.

## Wat het niet doet

- Het kijkt niet in je beheercentrum. Je zet alles zelf.
- Het blijft niet vanzelf actueel. Microsoft past deze regeling nog geregeld aan.
- Het rekent in dollars, zoals Microsoft. Wat het in euro's op je factuur wordt, hangt af van je contract.

## Licentie

MIT, zoals de rest van deze toolkit.
