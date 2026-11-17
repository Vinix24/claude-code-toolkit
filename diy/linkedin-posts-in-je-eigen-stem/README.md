# Hoe laat je Claude je LinkedIn-posts schrijven in je eigen stem?

Een klein team van skills dat elke week één LinkedIn-post met je maakt. Het haalt openingen uit de letterlijke woorden van je klanten, schrijft in jouw stem en laat een vaste controle de AI-taal meten. Op vrijdag rekent een script uit welk onderwerp je opschaalt, houdt of schrapt. Na elke stap stopt het tot jij akkoord geeft. Het plaatst niets.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/linkedin-posts-in-je-eigen-stem

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `prompt.md` | De lichte route: één prompt voor een project in Claude of ChatGPT, plus een vrijdagprompt. Niets te installeren |
| `commands/week.md` | `/week`: roept haken, concept en redacteur aan in vaste volgorde en stopt drie keer voor jouw akkoord |
| `skills/stem/` | Eén keer: `linkedin/stem.md` uit vijf tot tien teksten die je zelf schreef, met een citaat als bewijs bij elke regel. Zet ook de regels voor de redacteur klaar |
| `skills/haken/` | Haalt letterlijke klantzinnen uit je gespreksnotities en maakt er openingen van, elk met het nummer van zijn bron |
| `skills/concept/` | Schrijft de post bij de opening die jij kiest, plus een opdracht voor het beeld. Verzint geen feiten: wat ontbreekt krijgt `[CHECK]` |
| `skills/redacteur/` | Laat `slop-lint` de post meten en herschrijft alleen de zinnen die het aanwijst. Klantgegevens legt hij aan jou voor |
| `skills/vrijdag/` | `scripts/vrijdag.py` rekent per onderwerp: schalen, houden, schrappen of te weinig data. Zonder AI |
| `tests/` | Tests voor de vrijdagregel: `python3 -m unittest discover tests` |

Wat er in je eigen projectmap komt:

```
linkedin/
├── stem.md
├── logboek.csv
└── week-2026-W46/
    ├── notities.md        jij: gespreksnotities zonder namen
    ├── voorbeeld.md       jij, als je wilt: een post die je goed vond
    ├── 01-haken.md
    ├── 02-post.md
    ├── 02-beeld.md
    ├── 03-redactie.md
    └── 03-post.md         deze plaats je zelf
.claude/slop-lint.json     de regels voor de redacteur, met de namen van je klanten
```

## Zo gebruik je het

De kortste route: plak `prompt.md` in een project in Claude of ChatGPT.

De plugin is gemaakt voor Claude Code. In de Claude-app laden de skills en het commando ook, op elk betaald abonnement. De redacteur bouwt voort op `slop-lint`, een controle op AI-taal in Nederlandse tekst die zonder AI werkt. Installeer die ernaast:

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install slop-lint@claude-code-toolkit
/plugin install linkedin-redactie@claude-code-toolkit
```

In de Claude-app voeg je dezelfde marketplace toe onder Plugins in de zijbalk (heette eerder Customize). De scripts hebben Python 3.9 of nieuwer nodig, zonder extra pakketten.

Daarna:

1. Zeg "maak mijn stem" en plak vijf tot tien teksten die je zelf schreef.
2. Zet de namen van je klanten zelf in `.claude/slop-lint.json`, op de plek van `VERVANG-DOOR-KLANTNAMEN`.
3. Zet elke week je gespreksnotities in `linkedin/week-<JJJJ>-W<WW>/notities.md` en typ `/linkedin-redactie:week`.
4. Vul een week na het plaatsen de vertoningen en interacties in `linkedin/logboek.csv` in. Zeg op vrijdag "vrijdag".

Zelf iets vergelijkbaars maken? De skill-creator van Claude helpt je een eigen skill op te zetten. Begin met de kleinste: `vrijdag`.

## Wat het niet doet

- Het zoekt geen posts op LinkedIn en plaatst niets. Er is geen koppeling met LinkedIn.
- Het maakt geen beeld, alleen de opdracht ervoor.
- Je teksten en notities gaan naar de AI-leverancier van je assistent. Haal namen, bedragen en contactgegevens eruit voordat je ze aanlevert.

## Licentie

MIT, zoals de rest van de toolkit. `slop-lint` is een aparte plugin in dezelfde toolkit.
