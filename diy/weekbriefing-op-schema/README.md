<!--
Sjabloon voor de README van een case in de toolkit: diy/<slug>/README.md.
De werksessie vult hem in cases/<map>/toolkit/README.md. Na het akkoord van Vincent komt de map in de toolkit.
De toolkit is openbaar: geen namen, geen posttekst, geen link naar een comment-gate-post, geen casemateriaal.
Verwijder dit commentaarblok voor publicatie.
-->

# Hoe laat je Claude elke week vanzelf een briefing klaarzetten?

Een geplande taak in Claude zet elke week een briefing voor je klaar: te late facturen, nieuwe leads, je week, klantmail die niet kan wachten en drie contentideeën. Deze map helpt je die taak op te zetten op je eigen programma's. De taak leest, maakt alleen concepten en verstuurt niets. Een mail die iets van je wil, zet hij apart.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/weekbriefing-op-schema

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `opzet-prompt.md` | De prompt die je in Claude plakt. Hij vraagt eerst naar je bedrijf en je programma's. Daarna schrijft hij de opdracht voor je geplande taak, je rechtenkaart en de stappen |
| `rechtenkaart.md` | Wat de taak per onderdeel mag lezen en schrijven, waar je gegevens heen gaan en de proef voor de eerste nacht |

## Zo gebruik je het

1. Open Claude en kies "Cowork" in het berichtvak. In de nieuwe versie van Claude ontbreekt die keuze. Start daar een gewoon gesprek.
2. Plak de tekst uit `opzet-prompt.md` en beantwoord de vijf vragen.
3. Volg de stappen die je terugkrijgt. Doe de proef uit `rechtenkaart.md` voordat de taak voor het eerst 's nachts draait.

Je hebt een betaald Claude-abonnement nodig: geplande taken werken niet op het gratis abonnement.

Gebruik je QuickBooks, Xero, Zoho Books, MYOB of HubSpot? Kijk dan eerst naar de gratis plugin "small-business" van Anthropic, met een kant-en-klare maandagbriefing. Je vindt hem in Claude onder Plugins in de zijbalk (heette eerder Customize > Plugins > Discover), of op https://claude.com/plugins/small-business. De broncode staat op https://github.com/anthropics/knowledge-work-plugins/tree/main/small-business.

Wil je de briefing liever als eigen skill, een instructiebestand dat Claude opnieuw leest zodra de taak terugkomt? Dan helpt de skill-creator van Claude je die op te zetten.

## Wat het niet doet

- Het verstuurt, betaalt en beslist niets. Dat blijft jouw werk op maandag.
- Voor e-Boekhouden vond ik geen koppeling van het pakket zelf. Exact kondigt een eigen koppeling aan op zijn pagina met aankomende ontwikkelingen, zonder datum. Die van derde partijen heb ik niet getoetst. Zonder koppeling valt het onderdeel geld weg.
- Je mail, agenda en boekhouding gaan door de cloud van Anthropic.

## Licentie

Die van deze toolkit. De plugin "small-business" valt onder Apache-2.0 van Anthropic en zit niet in deze map.
