# Briefing-prompt

Plak alles in het blok hieronder in Claude of ChatGPT. Hij stelt eerst vragen en wacht op je antwoord. Daarna schrijft hij het briefingbestand.

```text
Je helpt me een marketingbriefing te maken. Dat is één bestand dat een AI-assistent leest voordat hij marketingwerk voor mijn bedrijf doet. Het volgt de opbouw van de open-source briefing-skill "product-marketing" uit github.com/coreyhaines31/marketingskills. Zo kunnen die skills het ook lezen.

Stap 1. Stel me deze vragen in één bericht en wacht op mijn antwoord.
- Wat verkoop ik, aan wie en tegen welke prijs ongeveer?
- Wie beslist bij mijn klant over de aankoop? Wie gebruikt het daarna?
- Wat kiest een klant als hij mij niet kiest? Niets doen of het zelf doen telt ook.
- Wat moet iemand doen nadat hij mijn marketing gelezen heeft?
- Adverteer ik betaald? Zo nee, dan laten we dat deel weg.
Vraag me ook om vijf echte stukken: twee klantmails, een offerte, een paar reviews en de tekst van mijn homepage. Zeg erbij dat ik namen, bedragen en contactgegevens eruit haal voordat ik plak.

Stap 2. Haal uit die stukken de letterlijke woorden van klanten. Hoe noemen ze het probleem? Hoe noemen ze mij? Welke bezwaren hebben ze? Citeer letterlijk en zet de bron erachter, zoals "mail 1" of "review 3".

Stap 3. Schrijf het bestand in het Nederlands met deze koppen. Laat de Engelse naam tussen haakjes staan, want de skills verwijzen naar die namen.

# Product Marketing Context
Document version: v1
Last updated: <datum van vandaag als JJJJ-MM-DD>
## Product (Product Overview)
## Doelgroep (Target Audience)
## Wie beslist (Personas)
## Problemen (Problems & Pain Points)
## Alternatieven (Competitive Landscape)
## Onderscheid (Differentiation)
## Bezwaren en wie niet past (Objections)
## Overstappen (Switching Dynamics)
## Klanttaal (Customer Language)
## Toon (Brand Voice)
## Bewijs (Proof Points)
## Doelen (Goals)
## Advertenties (Paid Ads), alleen als ik adverteer
## Lessen (Learnings), nog leeg
## Wijzigingen (Changelog), één regel: v1, dezelfde datum, eerste versie

Regels:
- Verzin geen citaten, cijfers, klantnamen of resultaten. Wat ontbreekt, schrijf je als "ONTBREEKT: <wat ik moet aanleveren>".
- Zet onder Toon: "Schrijf altijd in het Nederlands." Zet erbij of ik je of u gebruik, zoals in mijn eigen teksten.
- Houd het onder de twee pagina's.

Stap 4. Eindig met de lijst ONTBREEKT-punten, het belangrijkste eerst. Zeg daarna waar ik het bestand bewaar. Met de skills op mijn computer: als .agents/product-marketing.md in de map van mijn bedrijf. Zonder skills: als bestand in een Claude-project of een ChatGPT-project.
```

## Waar het vastloopt

- **Geen bronmateriaal geplakt.** Dan schrijft hij wat elk bedrijf over zichzelf zegt. Plak de stukken alsnog en vraag hem de klanttaal opnieuw te doen.
- **Veel ONTBREEKT-punten.** Dat is goed. Een briefing met drie gaten is bruikbaarder dan een met drie verzonnen citaten. Vul ze aan als je het materiaal hebt.
- **Bijwerken.** Plak de bestaande briefing en zeg wat er veranderde. Vraag om een nieuwe versie met één regel onder Wijzigingen: wat en waarom.
