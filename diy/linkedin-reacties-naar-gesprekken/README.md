# Hoe maak je met Claude van LinkedIn-reacties klantgesprekken?

Twee skills en een plak-prompt voor de stap na je post: van reactie naar gesprek en van gesprek naar klant. Claude maakt een berichtenreeks voor jouw klant die via je eigen asset naar een eerste stap leidt. Per reactie schrijft hij het volgende bericht, dat je zelf verstuurt. Je telt elke week vijf getallen. Een vaste rekenregel wijst één knelpunt aan, zonder AI. Er gaat niets automatisch naar LinkedIn.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/linkedin-reacties-naar-gesprekken

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `prompt.md` | De lichte route: één prompt voor een project in Claude of ChatGPT, plus een prompt voor een leadmagneet: de asset waar je reeks naartoe leidt. Niets te installeren |
| `trechter-sjabloon.csv` | Het lege logboek met de zes kolommen. Open het in Excel, Numbers of Google Sheets |
| `skills/trechter/` | `scripts/trechter.py` telt vier weken op en zegt welke stap lekt. Zonder AI |
| `skills/dm/` | Maakt één keer een basisreeks op je eigen klant, van reactie via je asset naar de eerste stap. Daarna per persoon een eigen reeks uit zijn reactie en profiel, en antwoorden op bezwaren uit je eigen lijst. Jij verstuurt alles |
| `.claude-plugin/plugin.json` | Zodat je de twee skills in Claude Code als plugin installeert |
| `tests/` | Tests voor de rekenregel: `python3 -m unittest discover tests` |

## Zo gebruik je het

**De kortste route.** Plak de eerste prompt uit `prompt.md` als instructie in een project in Claude of ChatGPT. Tel elke week vijf getallen en plak ze erin.

**Met de skills, in de Claude-app of op claude.ai.** Het helpcentrum van Anthropic noemt skills op elk plan, ook het gratis plan. Code-uitvoering moet aanstaan: Settings > Capabilities, "Code execution and file creation". In de nieuwe indeling van Settings heet die schakelaar "Create and edit files".

1. Download deze repo als ZIP (knop Code > Download ZIP) en pak hem uit.
2. Maak van de map `diy/linkedin-reacties-naar-gesprekken/skills/trechter` een ZIP-bestand. Zip de map zelf, niet de bestanden erin: de skillmap moet bovenaan in de ZIP staan. Doe hetzelfde met `skills/dm`.
3. Upload ze bij Customize > Skills. Klik op de plusknop, kies "+ Create skill" en daarna "Upload a skill".
4. Bewaar je logboek zelf, in Excel of Google Sheets, met de kolommen uit `trechter-sjabloon.csv`. Upload het elke week als CSV in het gesprek en zeg "trechter".

In de Claude-app kan het ook als plugin: Customize > Plugins > Add > "Add marketplace", met `Vinix24/claude-code-toolkit`. Plugins in de app vragen een betaald abonnement.

**In Claude Code installeer je de plugin zo:**

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install linkedin-gesprekken@claude-code-toolkit
```

Het script heeft Python 3.9 of nieuwer nodig, zonder extra pakketten. Daarna, in Claude Code:

1. Zet `trechter-sjabloon.csv` als `linkedin/trechter.csv` in je projectmap. Vul elke week één regel in. Zet een streepje op het moment dat je op een reactie antwoordt; op vrijdag tel je alleen op.
2. Zeg "trechter". Je krijgt een tabel en één knelpunt.
3. Zeg "reeks". De skill `dm` vraagt naar je klant, zijn bezwaren met jouw antwoorden en je asset. Daarna schrijft hij `linkedin/klantprofiel.md`, `linkedin/bezwaren.md` en `linkedin/reeks.md`.
4. Reageerde iemand uit je doelgroep of vroeg hij om je asset? Zeg "dm" en plak zijn reactie en wat je uit zijn profiel haalt: functie, bedrijf, branche, waar hij over schrijft. Geen naam of contactgegevens. Je krijgt zijn eigen reeks in `linkedin/personen/<label>.md`.
5. Antwoordt hij? Plak zijn antwoord met het label. Staat zijn bezwaar nog niet in je lijst? Dan vraagt de skill eerst wat jij daarop antwoordt. Verwijder het bestand van een persoon als het gesprek klaar is.

Wat je telt: mensen die een reactie schreven onder je posts, hoeveel daarvan uit je doelgroep, gesprekken met iemand uit je doelgroep die reageerde en terugschreef, afspraken uit die gesprekken en klanten uit die afspraken. Klanten telt de regel over twaalf weken. Een opdracht volgt vaak weken na de afspraak.

Met de [LinkedIn-redactie](../linkedin-posts-in-je-eigen-stem/) uit deze toolkit staan beide logboeken in dezelfde map `linkedin/`. Een [marketingbriefing](../marketingbriefing-voor-claude/) in `.agents/product-marketing.md` leest de skill `dm` als eerste.

Zie je zo'n post vaker? Pluis hem zelf uit met de skill [reverse-engineer](../../reverse-engineer/) in deze toolkit. Die doet wat hier gebeurde: hij kiest de vorm en vindt het lastige stuk.

Zelf iets vergelijkbaars maken? De skill-creator van Claude helpt je een eigen skill op te zetten. Begin met de kleinste: `trechter`.

## Wat het niet doet

- Het leest niets van LinkedIn en verstuurt niets. Je telt en verstuurt zelf. Geen koude benadering, geen connectieverzoeken en geen reeksen naar profielbezoekers.
- Berichten die binnenkomen zonder reactie op een post telt het niet.
- De grenzen in de rekenregel zijn startwaarden, geen benchmark. Pas ze aan als je eigen cijfers iets anders laten zien.
- Wat je plakt, gaat naar de AI-leverancier van je assistent. Plak reacties zonder naam of profiellink. Kijk in je privacyinstellingen of je gesprekken gebruikt worden om het model te trainen.

## Licentie

MIT, zoals de rest van de toolkit.
