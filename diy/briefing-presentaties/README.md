# Hoe brief je Claude zodat je presentatie er niet uitziet als die van iedereen?

Twee prompts en een skill waarmee Claude een pitchdeck, offerte, salespresentatie, onepager, LinkedIn-carrousel, flyer, handboek of kwartaalupdate maakt die op jouw bedrijf lijkt. Claude vraagt eerst naar je situatie, je huisstijl en de feiten die alleen jij kent. Daarna laat hij de opbouw zien en pas dan bouwt hij. Hij verzint geen cijfers: wat ontbreekt staat als invulvak in het stuk, met een lijstje eronder waar elk getal vandaan komt.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/briefing-presentaties

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `huisstijl-prompt.md` | Plak-prompt die je huisstijl vastlegt in een blok van zes regels. Eén keer doen |
| `briefing-prompt.md` | Plak-prompt voor elk nieuw stuk: situatie, ontbrekende gegevens, opbouw, bouwen, bonnetje |
| `skills/briefing/SKILL.md` | Dezelfde werkwijze als skill, zodat je niets meer hoeft te plakken |
| `skills/briefing/references/stukken.md` | De vaste velden en bouwregels voor de acht soorten stukken |
| `skills/briefing/references/huisstijl-interview.md` | Wat de skill vraagt als je nog geen huisstijlblok hebt |
| `.claude-plugin/plugin.json` | Zodat je de skill in Claude Code als plugin installeert |

## Zo gebruik je het

**De kortste route.** Plak `huisstijl-prompt.md` in een nieuw gesprek in Claude en bewaar het blok dat eruit komt. Plak bij elk nieuw stuk dat blok plus `briefing-prompt.md`. Werkt op elk Claude-plan, ook het gratis plan. In ChatGPT werken de vragen net zo; het bouwen van slides en ontwerpen gaat daar anders.

**Maak je elke week een deck of offerte? Gebruik de skill.**

In de Claude-app of op claude.ai:

1. Zet code-uitvoering aan bij je instellingen. Zonder die instelling werken skills niet.
2. Download deze repo als ZIP (knop Code > Download ZIP) en pak hem uit.
3. Wil je je huisstijl niet steeds plakken, zet je blok dan als `mijn-huisstijl.md` in de map `diy/briefing-presentaties/skills/briefing`.
4. Maak van de map `briefing` een ZIP-bestand en upload dat bij Customize, onder Skills.

In Claude Code:

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install briefing-presentaties@claude-code-toolkit
```

Zet je huisstijlblok daar als `mijn-huisstijl.md` in de map waar je werkt.

Zelf iets vergelijkbaars maken? De skill-creator van Claude helpt je een eigen skill op te zetten. Zeg bijvoorbeeld: "Maak een skill van deze briefing en mijn huisstijlblok."

## Wat het niet doet

- Een huisstijl of merk ontwerpen. Zonder huisstijl werkt het met een neutrale stijl en zegt het dat erbij.
- Drukklaar werk garanderen. Vraag je drukker welke afloop en welk kleurprofiel hij wil.
- Een juridische toets op een offerte of handboek.

## Licentie

MIT, net als de rest van deze toolkit.
