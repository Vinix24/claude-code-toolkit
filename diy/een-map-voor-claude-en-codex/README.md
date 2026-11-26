# Hoe gebruik je één map voor Claude en Codex, zodat je niet vastzit aan één AI-leverancier?

Eén prompt die een map waarin Claude al werkt, leesbaar maakt voor een tweede assistent. Je huisregels krijgen een tweede naam, je skills een tweede plek en je ziet in één tabel wat meereist en wat niet. Het slot reist niet mee. De prompt gaat ook na of iets wat de tweede leverancier niet mag zien, nog in je vangnet staat.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/een-map-voor-claude-en-codex

**Heb je de map nog niet?** Begin bij https://vincentvandeth.nl/blog/van-claude-chat-naar-claude-code. De prompts en het slot daarvoor staan in [de map ernaast](../van-claude-chat-naar-claude-code/).

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `draagbaar-prompt.md` | De prompt. Geeft je huisregels de naam `AGENTS.md`, kopieert je skills naar `.agents/skills` en telt na wat meereist. Stelt eerst vier vragen |
| `gids/een-map-twee-assistenten.pdf` | De uitleg in acht pagina's, voor wie liever kijkt dan leest |

## Zo gebruik je het

1. Open je map `Bedrijf` in het tabblad Code van de Claude-app. Zet de keuzeknop onder het tekstvak op Manual.
2. Plak de prompt uit `draagbaar-prompt.md` en beantwoord de vier vragen.
3. Zet bij de tweede leverancier de schakelaar voor training uit. Bij OpenAI staat hij op Free, Plus en Pro standaard aan: Settings, Data controls, "Improve the model for everyone".
4. Haal uit de map wat een tweede leverancier niet mag zien. De map `prive` zelf en `prive/proef.txt` laat je staan: daarmee toets je je slot. Zegt de prompt dat iets nog in je vangnet staat, open dan in de andere app een kopie van je map zonder de map `.git`.
5. Laat Claude een foto maken. Open de map daarna in de andere app. Zet daar de knop voor rechten op de stand die om akkoord vraagt. Vraag: wat zijn mijn huisregels?

Plak de prompt opnieuw na een nieuwe skill en anders eens per maand. De controle laat dan zien wat uit elkaar liep.

Zie je zo'n post vaker? Pluis hem zelf uit met de skill [reverse-engineer](../../reverse-engineer/) in deze toolkit. Die doet wat hier gebeurde: hij kiest de vorm en vindt het lastige stuk.

## Wat het niet doet

- Het slot van Claude reist niet mee. Reken erop dat je privémap in de andere app open staat. Codex wijzigt volgens OpenAI binnen je map zonder te vragen. De knop voor rechten daar kiest wanneer de assistent om akkoord vraagt. Een slot op een map is dat niet.
- Wat ooit op een foto in je vangnet stond, staat nog in de map `.git`. Weghalen uit de map is dan niet genoeg.
- Een skill staat daarna op twee plekken. Die blijven alleen gelijk als de assistent zich aan de afspraak in je huisregels houdt. Wijzig je skills alleen in Claude: bij Codex is de map `.agents` volgens OpenAI alleen-lezen.
- De kant van Claude is getoetst op een Mac. Alles over Codex komt uit de documentatie van OpenAI en is niet in die app getoetst. Op Windows is niets getoetst.
- De namen van knoppen en menu's bij OpenAI zijn nagekeken op 26 november 2026. Ze kunnen veranderen.

## Licentie

Dezelfde licentie als de rest van deze toolkit. Zie het bestand `LICENSE` in de hoofdmap.
