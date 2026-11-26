# Hoe stap je over van de Claude-chat naar Claude Code, zonder te programmeren?

Prompts en een kant-en-klaar slot waarmee je van losse gesprekken in de chat naar één map op je computer gaat. In die map leest Claude bij elke sessie wie je bent en waar alles staat. Wat privé is, zit op slot. Elke wijziging draai je terug. Je huisregels staan in een formaat dat ook andere assistenten lezen.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/van-claude-chat-naar-claude-code

**Eén map voor Claude en Codex:** https://vincentvandeth.nl/blog/een-map-voor-claude-en-codex. De prompt daarvoor staat in [de map ernaast](../een-map-voor-claude-en-codex/).

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `verhuizing-prompt.md` | Prompt 1. Richt je map in: een `CLAUDE.md` per project en voor de hoofdmap, het vangnet en het slot. Stelt eerst vijf vragen over je bedrijf |
| `eerste-skill-prompt.md` | Prompt 2. Maakt na een week je eerste eigen skill van een taak die steeds terugkomt |
| `settings.json` | Het slot, kant-en-klaar. Regels die de map `prive` weigeren en vragen bij de gewone commando's voor verwijderen, verplaatsen en uploaden. Plus de sandbox |
| `alleen-het-slot-prompt.md` | Een korte prompt voor wie alleen het slot wil. Zet eerst git op en daarna het slot |
| `spiekbrief.md` | Eén pagina voor naast je scherm: de vaste volgorde, de vier lagen, de vijf standen en wat je doet als het misgaat |
| `gids/van-de-chat-naar-een-map.pdf` | De hele handleiding in 16 pagina's, om door te bladeren of te delen |

## Zo gebruik je het

1. Installeer de Claude-app en open het tabblad Code. Je hebt een betaald abonnement nodig.
2. Maak een lege map `Bedrijf` met daarin een map `projecten`. Open `Bedrijf` via "Open folder…".
3. Zet de keuzeknop onder het tekstvak op Manual.
4. Plak de prompt uit `verhuizing-prompt.md` en beantwoord de vijf vragen.
5. Start daarna een nieuwe sessie en stel de drie vragen waar de prompt mee eindigt. Zo zie je zelf of je huisregels geladen zijn en of het slot werkt.

Wil je alleen het slot? Plak dan de korte prompt uit `alleen-het-slot-prompt.md`. Zelf een map `.claude` maken lukt op een Mac niet: Finder weigert een naam die met een punt begint. Op Windows werkt de sandbox niet. Zet daar niets wat privé is in de map.

Zie je zo'n post vaker? Pluis hem zelf uit met de skill [reverse-engineer](../../reverse-engineer/) in deze toolkit. Die doet wat hier gebeurde: hij kiest de vorm en vindt het lastige stuk.

Zelf een skill maken gaat met prompt 2. Anthropic heeft daarnaast een eigen hulpje dat je door het opzetten leidt. In de app klik je op de plus naast het tekstvak en kies je Add plugins. Staat er Plugins in plaats van Add plugins, kies dan Plugins en daarna Browse plugins. Zoek daar skill-creator. In de terminal installeer je het met:

```
/plugin install skill-creator@claude-plugins-official
```

## Wat het niet doet

- Reken erop dat je chatgesprekken in de chat blijven. Mee komen je bestanden en je instructies.
- Het slot werkt alleen als je de map `Bedrijf` zelf opent. In een submap geldt het niet.
- De sandbox werkt op een Mac. Op Linux heeft hij extra hulpprogramma's nodig. Op gewone Windows werkt hij niet. Daar blijven alleen de regels over. Ook die zijn op Windows niet getoetst.
- Wat Claude nooit mag zien, hoort niet in de map. Buiten de map komt hij er niet toevallig langs. Echt onbereikbaar is alleen wat niet op deze computer staat.
- Het slot hangt aan de naam van de map `prive`. Hernoem of verplaats die map nooit.
- Het slot geldt alleen in Claude Code: in het tabblad Code, in de terminal en in VS Code. Open je de map met de gewone Claude of met een andere assistent, haal dan eerst uit de map wat privé is.
- Git is een vangnet en geen back-up. Wat op slot zit, staat niet op de foto.
- Het slot is getoetst in de motor van Claude Code en met drie vragen in de Claude-app, op een Mac. Op Windows is niets getoetst. Alles over Codex komt uit de documentatie van OpenAI.

## Licentie

Dezelfde licentie als de rest van deze toolkit. Zie het bestand `LICENSE` in de hoofdmap.
