# Hoe laat je AI een website maken die niet op een AI-site lijkt?

Twee prompts voor Claude of ChatGPT. De eerste werkt je briefing uit tot ontwerpkeuzes en toetsen: elke eis wordt een vraag met ja of nee. De tweede bouwt een proefversie van je homepage als één bestand. Daarna kijk je zelf na of de pagina je toetsen haalt.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/ai-website-die-niet-op-ai-lijkt

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `werkwijzeprompt.md` | Stap 1. Leest je briefing, vraagt hooguit vijf dingen die ontbreken en schrijft de uitgewerkte briefing met toetsen |
| `bouwprompt.md` | Stap 2. Bouwt de homepage als één `index.html`. Met de correctieprompt voor stap 3 |

## Zo gebruik je het

1. Begin een nieuw gesprek in Claude of ChatGPT. Plak `werkwijzeprompt.md` met je briefing eronder. Heb je geen briefing, schrijf dan vijf regels: wat je doet, voor wie, wat een bezoeker moet doen, welk eigen beeld je hebt en wat nooit mag.
2. Begin een nieuw gesprek. Plak `bouwprompt.md` met je eigen bestanden en de uitgewerkte briefing erin.
3. Sla de code op als `index.html` naast je bestanden en open hem op je telefoon. Loop de toetsen langs. Haalt de pagina er een paar niet, gebruik dan de correctieprompt onderaan `bouwprompt.md`.

Wil je er een vaste werkwijze van maken die je assistent elke keer volgt? De skill-creator van Claude helpt je een eigen skill op te zetten.

## Wat het niet doet

- Smaak toetsen. Die beoordeel je met het oog, of je huurt een dag art direction in.
- Een site opleveren die klaar is voor klanten. Het is een proefversie: geen onderhoud, geen hosting van video, geen beveiligingstoets.
- Je briefing privé houden. Hij gaat naar de leverancier van je chat. Zet er geen gegevens van klanten in.

## Licentie

Valt onder de licentie van de toolkit. Zie `LICENSE` in de hoofdmap.
