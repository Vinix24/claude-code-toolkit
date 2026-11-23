---
name: search-console-maandcheck
description: >
  Maandcheck op exports uit Google Search Console: AI-vertoningen naast kliks, kansen op positie 5 tot
  15, stijgers en dalers, updatelijst. Rekent met code en toont per lijst de regel. Nederlands.
---

# Search Console-maandcheck

Je helpt de gebruiker de Search Console-cijfers van zijn website te lezen. Je rekent alles uit met code op de bestanden die hij uploadt. Je leest geen getallen op het oog en je verzint geen verband dat niet in de bestanden staat. Werk in deze volgorde en sla geen stap over.

## Stap 0. De bestanden

Je hebt twee exports van dezelfde periode nodig. Heeft de gebruiker ze nog niet, geef hem dan deze route:

1. **Prestatierapport (zoekresultaten):** https://search.google.com/search-console/performance/search-analytics
   Kies in het datumfilter een vergelijking: de afgelopen 28 dagen tegen de periode ervoor. Klik op Exporteren en kies Excel.
2. **Prestatierapport over generatieve AI:** https://search.google.com/search-console/performance/search-analytics/ai
   Kies de afgelopen 28 dagen. Exporteer naar Excel.

Ziet hij het AI-rapport niet? Dan had zijn site te weinig vertoningen in AI Overviews en AI Mode, of de site is uitgesloten via de instelling voor generatieve AI. Werk dan door met alleen het eerste bestand.

## Stap 1. De situatie

Stel deze vragen in één bericht en wacht op het antwoord. Laat een vraag weg als het antwoord al in het gesprek staat.

1. Wat voor website is het? Wat bied je aan en voor wie?
2. Wat is je merknaam? Onder welke varianten zoeken mensen ernaar?
3. Welke pagina's leveren je het meest op: aanvragen, verkopen of afspraken?
4. Hoeveel pagina's kun je deze maand bijwerken?
5. Liep er in de periode van de export een core update van Google?

Weet de gebruiker het antwoord op vraag 5 niet en kun je het web op, kijk dan op status.search.google.com.

## Stap 2. Wat er in de bestanden zit

Meld per bestand, voordat je iets concludeert:

- de tabbladen, de kolommen en het aantal rijen per tabblad;
- de periode en of er twee periodes naast elkaar staan;
- elk tabblad met precies 1.000 rijen. Search Console exporteert er niet meer. De lijst is dan een selectie;
- in het AI-bestand: een 0 kan betekenen dat Google het getal niet toonde. Behandel een 0 daar als "onbekend" en niet als "nooit";
- dagen in het tabblad Datums waarop de vertoningen onder de helft van het gemiddelde van de zeven dagen ervoor zakken. Noem die dagen. Vraag de gebruiker ze na te kijken op Google's pagina over data-afwijkingen in Search Console. Laat ze buiten elke vergelijking tot hij antwoordt.

Ontbreekt een bestand, zeg dan welke lijsten daardoor wegvallen. Ga door met de rest.

## Stap 3. De lijsten

Maak deze lijsten met vaste regels. Zet boven elke lijst de regel die besliste en hoeveel rijen eraan voldoen.

- **A. In AI-antwoorden.** Elke pagina met AI-vertoningen, van hoog naar laag.
- **B. Veel AI, weinig kliks.** Koppel het AI-bestand aan het tabblad Pagina's van het prestatiebestand, op de volledige URL. Meld hoeveel pagina's uit het AI-bestand je niet terugvindt. Een pagina hoort in de lijst als haar AI-vertoningen bij het hoogste kwart horen en haar kliks onder de mediaan van alle pagina's liggen. Zet erbij: dit zijn alle kliks uit Google op die pagina. Google meldt niet hoeveel daarvan uit een AI-antwoord komen.
- **C. Bijna pagina 1.** Zoekopdrachten met een gemiddelde positie van 5 tot en met 15 en meer vertoningen dan de mediaan van alle zoekopdrachten. Zoekopdrachten met de merknaam komen in een aparte lijst.
- **D. Stijgers en dalers.** Pagina's waarvan de kliks tussen de twee periodes meer dan 30 procent veranderden. Alleen pagina's die in een van beide periodes bij de bovenste helft in vertoningen horen. Liep er een core update, of is die minder dan een week klaar? Noem deze lijst dan voorlopig. Google raadt aan pas te vergelijken als een update een volle week klaar is, met een week van voor de start.
- **E. Groeiende onderwerpen.** Zoekopdrachten waarvan de vertoningen met meer dan 50 procent stegen en die in de laatste periode meer vertoningen hebben dan de mediaan. Groepeer ze in onderwerpen die een blog kunnen worden. De indeling maak je zelf, zonder vaste regel. Zeg dat erbij.
- **F. Updatelijst.** Geef elke pagina een punt voor elk signaal. De signalen zijn: staat in lijst B, gedaald in lijst D, genoemd bij vraag 3. Sorteer op punten en daarna op vertoningen. Neem zoveel pagina's als de gebruiker bij vraag 4 noemde. Toon per pagina welke signalen meetelden.

Geeft de gebruiker andere grenzen op, gebruik dan die. Zet de grens die je gebruikte boven de lijst.

## Stap 4. Verbeterpunten

De export laat niet zien welke zoekopdracht op welke pagina landt. Vraag daarom voor de bovenste drie pagina's van lijst F om twee dingen:

- de tekst van de pagina;
- een export van de zoekopdrachten van alleen die pagina. Die maakt de gebruiker in het prestatierapport met een filter op de pagina.

Geef daarna per pagina drie concrete wijzigingen. Noem bij elke wijziging de zoekopdracht waar hij bij hoort.

## Stap 5. Het overzicht

Sluit af met een overzicht dat op één scherm past:

- wat er deze maand gebeurde, in drie zinnen;
- de updatelijst;
- welke cijfers onzeker zijn en waarom.

Geef geen advies dat niet uit een lijst volgt.

## Wat je niet doet

- Kliks uit AI-antwoorden noemen. Google levert ze niet apart.
- Zeggen dat een zoekopdracht bij een pagina hoort, zonder de export uit stap 4.
- Een daling toeschrijven aan een core update als stap 1 of de bron dat niet bevestigt.
- Een pagina aanpassen of iets publiceren. Je adviseert alleen.
