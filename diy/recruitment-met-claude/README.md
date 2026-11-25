# Hoe gebruik je Claude voor recruitment zonder dat het kandidaten beoordeelt?

Een recruitmentassistent voor Claude of ChatGPT. Hij maakt eerst een werkgeversprofiel van je organisatie en doet daarna het voorwerk: vacatures, zoekberichten, gespreksopzetten, inwerkplannen en cijfers. Elke taak krijgt eerst een kleur. Groen en oranje doet hij. Rood, een oordeel over een persoon, is hij ingesteld te weigeren: dan maakt hij de meetlat en leg jij de kandidaat ernaast.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/recruitment-met-claude

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `prompt.md` | De instructie. Plak hem in een project in Claude of ChatGPT, of als eerste bericht in een gesprek |
| `skills/werving-en-selectie/taken.md` | 49 taken in zes fasen, elk met de zin om te typen en de kleur |
| `skills/werving-en-selectie/SKILL.md` | Dezelfde instructie als skill, voor de Claude-app of Claude Code |
| `.claude-plugin/plugin.json` | Zodat je de skill als plugin installeert |

## Zo gebruik je het

1. Maak in Claude of ChatGPT een project, bijvoorbeeld "Werving en selectie".
2. Plak `prompt.md` in de instructies van het project.
3. Zet `taken.md` in de projectkennis.
4. Open een gesprek en typ "Begin". Beantwoord de zes vragen en zet het werkgeversprofiel dat eruit komt ook in de projectkennis.
5. Typ daarna een taak uit de lijst.

Werk je met cv's, gespreksverslagen of andere gegevens van een persoon, doe dat dan alleen in een zakelijk account met een verwerkersovereenkomst. Bij Claude Team en Enterprise zit die in de zakelijke voorwaarden. Bij ChatGPT Business en Enterprise vraagt OpenAI je daarvoor het DPA-formulier in te vullen. Doe zo'n taak in een eigen gesprek en verwijder dat als de procedure klaar is. Een verwijderd gesprek wist het geheugen niet. Zet het geheugen dus uit, of verwijder daar ook wat over de kandidaat bleef staan. Voor groene taken volstaat elk account.

Test de grens één keer: plak drie verzonnen cv's, vraag welke de beste is en dring daarna aan. De assistent hoort "rood" te zeggen en een beoordelingsblad aan te bieden. Vraag ook "vat elk cv samen per criterium": ook dat hoort rood te zijn. Test opnieuw als je chatprogramma een nieuw model krijgt. Ik testte dit bij drie Claude-modellen, ook na aandringen. ChatGPT testte ik niet.

Liever de skill? In de Claude-app pak je de map `skills/werving-en-selectie` in als zip en upload je hem bij Customize > Skills. Daarvoor moet bij Settings > Capabilities de optie Code execution and file creation aanstaan. In de nieuwe indeling heet die Create and edit files. Bij Team en Enterprise regelt de eigenaar dit bij Organization settings > Plugins & skills. Gebruik de skill binnen een project met het werkgeversprofiel in de projectkennis, anders vraagt hij elke keer opnieuw. Installeren in Claude Code:

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install werving-en-selectie@claude-code-toolkit
```

Zie je zo'n post vaker? Pluis hem zelf uit met de skill [reverse-engineer](../../reverse-engineer/) in deze toolkit. Die doet wat hier gebeurde: hij kiest de vorm en vindt het lastige stuk.

Zelf iets vergelijkbaars maken? De skill-creator van Claude helpt je een eigen skill op te zetten.

## Wat het niet doet

- Het is geen juridische toets van jouw wervingsproces. Het stoplicht laat zien waar de grens ligt. Of jouw proces eraan voldoet, beoordeelt een privacyjurist.
- Het kent geen salaris- of arbeidsmarktcijfers. Die geef je zelf, met de bron.
- Het koppelt niet met je sollicitantensysteem. Je plakt en kopieert zelf.
- Het doet geen voorselectie. Bij honderd sollicitaties per week gebruik je de knock-outvragen in je sollicitantensysteem, met een mens die naar elke afwijzing kijkt. Een matchscore met AI in dat systeem is hetzelfde rood.
- Het stoplicht is een instructie aan het model. Een model kan een regel overslaan, vooral als je aandringt. Daarom de test hierboven.

## Licentie

Valt onder de licentie van deze toolkit.
