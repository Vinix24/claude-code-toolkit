---
name: briefing
description: >
  Maakt samen met de gebruiker één presentatie, document of ontwerp via een vaste briefing: eerst de
  situatie en de huisstijl, dan de vaste velden per soort stuk, eerst de opbouw en pas daarna bouwen.
  Verzint geen cijfers, namen of prijzen en zet onder elk stuk een bonnetje met de herkomst. Voor een
  pitchdeck, offerte, salespresentatie per klantsegment, onepager, LinkedIn-carrousel, flyer of poster,
  handboek voor nieuwe medewerkers of kwartaalupdate. Gebruik bij "maak een presentatie", "maak een
  deck", "maak een offerte", "zet dit in slides", "ontwerp een flyer", "maak een onepager", of wanneer
  iemand een van deze stukken wil laten maken. Antwoordt in het Nederlands.
---

# Briefing: één stuk dat eruitziet als dat van de gebruiker

Standaardwerk komt van ontbrekende input. Deze skill haalt die input eerst op en bouwt pas daarna. Werk in deze volgorde. Sla geen stap over, ook niet als de gebruiker haast heeft. Vraag hooguit of hij een stap bewust wil overslaan.

## Stap 0. De huisstijl vinden

Zoek het huisstijlblok in deze volgorde:

1. in het gesprek;
2. in een bestand `mijn-huisstijl.md` in de map van deze skill of in de map waar de gebruiker werkt;
3. in de projectinstructies.

Vind je niets, vraag dan of de gebruiker een blok heeft. Heeft hij er geen, volg dan `references/huisstijl-interview.md`. Geef het blok daarna terug met één zin: "Bewaar dit blok. Plak het bij je volgende stuk in het gesprek, of zet het als `mijn-huisstijl.md` in de map van deze skill." Werkt de gebruiker met een betaald plan, zeg dan ook dat hij het in Claude Design kan vastleggen als design system.

Wil hij nu geen huisstijl maken, werk dan met een rustige, neutrale stijl en zeg dat erbij.

## Stap 1. De situatie

Stel deze vragen in één bericht. Wacht op het antwoord.

1. Wat voor bedrijf heb je en wie zijn je klanten?
2. Welk stuk maak je? Noem de acht stukken uit `references/stukken.md`, of laat de gebruiker het zelf beschrijven.
3. Wie gaat het lezen of zien? Wat moet die persoon daarna doen?
4. Presenteer je het zelf, of leest de ander het zonder jou?
5. Waar moet het heen: PowerPoint, PDF, Word, Google Docs of de drukker?

Laat een vraag weg als het antwoord al in het gesprek staat.

## Stap 2. Wat ontbreekt

Lees in `references/stukken.md` de vaste velden van het gekozen stuk. Check welke de gebruiker al gaf. Vraag wat ontbreekt in één bericht, hooguit zes vragen. Wacht op het antwoord. Is alles er al, ga dan door.

Beschrijft de gebruiker een stuk dat niet in de lijst staat, stel dan zelf de velden op volgens hetzelfde patroon: doel, lezer, de feiten die alleen hij kent, de vorm. Laat hem die lijst eerst bevestigen.

## Stap 3. De opbouw

Geef alleen de titels van de slides of de koppen van het document. Wacht op een akkoord. Dit spaart limiet: een verhaal dat niet klopt, zie je aan de titels voordat er iets ontworpen is.

## Stap 4. Bouwen

Maak een presentatie als slides, een tekst als document, een flyer of poster als ontwerp. Volg de regels per stuk uit `references/stukken.md`. Daarnaast geldt altijd:

- Gebruik alleen de kleuren en lettertypen uit het huisstijlblok.
- Elke slidetitel is een conclusie in een hele zin. Wie alleen de titels leest, kent het verhaal.
- Verzin geen cijfers, namen, klanten, citaten of prijzen. Ontbreekt iets, zet dan `[INVULLEN: wat er moet staan]` in het stuk, in de accentkleur.
- Reken je iets uit, zoals een groei in procenten, laat dan de berekening zien in het bonnetje.

## Stap 5. Het bonnetje

Zet onder het resultaat:

- elk getal en elke claim, met de herkomst: "van jou", "berekend uit ..." of `[INVULLEN]`
- wat je bewust hebt weggelaten
- de twee dingen die de gebruiker als eerste moet controleren

Sluit af met: "Werk elk [INVULLEN] weg voordat het stuk de deur uitgaat."

## Wat je nooit doet

- Een cijfer, naam, klant, citaat of prijs verzinnen. Ook niet als voorbeeld.
- Een huisstijl verzinnen en die presenteren als die van de gebruiker.
- Het stuk versturen, delen of publiceren. Dat doet de gebruiker zelf.
- Wachtwoorden, inlogcodes of persoonsgegevens van medewerkers in een stuk zetten. Vraag de gebruiker die weg te laten.
