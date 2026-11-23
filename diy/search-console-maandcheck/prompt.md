# Plak-prompt: de maandcheck op je Search Console-cijfers

Werkt in Claude op elk plan, ook het gratis plan. Code-uitvoering moet aanstaan (Instellingen, Capabilities). In ChatGPT werkt hij ook, in een gesprek waarin je bestanden kunt uploaden.

## Eerst twee exports, van dezelfde periode

1. **Prestatierapport (zoekresultaten):** https://search.google.com/search-console/performance/search-analytics
   Kies in het datumfilter een vergelijking: de afgelopen 28 dagen tegen de periode ervoor. Klik op Exporteren en kies Excel.
2. **Prestatierapport over generatieve AI:** https://search.google.com/search-console/performance/search-analytics/ai
   Kies de afgelopen 28 dagen. Exporteer naar Excel.

Zie je het AI-rapport niet? Dan had je site te weinig vertoningen in AI Overviews en AI Mode, of je site is uitgesloten via de instelling voor generatieve AI.

Upload beide bestanden in een nieuw gesprek en plak daaronder de prompt.

## De prompt

```text
Je helpt me de Search Console-cijfers van mijn website te lezen. Ik upload twee exports uit Google Search Console. Reken alles uit met code op die bestanden. Lees geen getallen op het oog. Verzin geen verband dat niet in de bestanden staat.

Stap 1. Stel me eerst deze vragen in één bericht en wacht op mijn antwoord.
1. Wat voor website is het? Wat bied je aan en voor wie?
2. Wat is je merknaam? Onder welke varianten zoeken mensen ernaar?
3. Welke pagina's leveren je het meest op: aanvragen, verkopen of afspraken?
4. Hoeveel pagina's kun je deze maand bijwerken?
5. Liep er in de periode van de export een core update van Google?
Weet ik het antwoord op vraag 5 niet en kun je het web op, kijk dan op status.search.google.com.

Stap 2. Kijk wat er in de bestanden zit voordat je iets concludeert. Meld per bestand:
- de tabbladen, de kolommen en het aantal rijen per tabblad;
- de periode en of er twee periodes naast elkaar staan;
- elk tabblad met precies 1.000 rijen. Search Console exporteert er niet meer. De lijst is dan een selectie;
- in het AI-bestand: een 0 kan betekenen dat Google het getal niet toonde. Behandel een 0 daar als "onbekend" en niet als "nooit";
- dagen in het tabblad Datums waarop de vertoningen onder de helft van het gemiddelde van de zeven dagen ervoor zakken. Noem die dagen. Vraag me ze na te kijken op Google's pagina over data-afwijkingen in Search Console. Laat ze buiten elke vergelijking tot ik antwoord.
Ontbreekt een bestand, zeg dan welke lijsten daardoor wegvallen. Ga door met de rest.

Stap 3. Maak deze lijsten met vaste regels. Zet boven elke lijst de regel die besliste en hoeveel rijen eraan voldoen.
A. In AI-antwoorden: elke pagina met AI-vertoningen, van hoog naar laag.
B. Veel AI, weinig kliks: koppel het AI-bestand aan het tabblad Pagina's van het prestatiebestand, op de volledige URL. Meld hoeveel pagina's uit het AI-bestand je niet terugvindt. Een pagina hoort in de lijst als haar AI-vertoningen bij het hoogste kwart horen en haar kliks onder de mediaan van alle pagina's liggen. Zet erbij: dit zijn alle kliks uit Google op die pagina. Google meldt niet hoeveel daarvan uit een AI-antwoord komen.
C. Bijna pagina 1: zoekopdrachten met een gemiddelde positie van 5 tot en met 15 en meer vertoningen dan de mediaan van alle zoekopdrachten. Zoekopdrachten met mijn merknaam komen in een aparte lijst.
D. Stijgers en dalers: pagina's waarvan de kliks tussen de twee periodes meer dan 30 procent veranderden. Alleen pagina's die in een van beide periodes bij de bovenste helft in vertoningen horen. Liep er een core update, of is die minder dan een week klaar? Noem deze lijst dan voorlopig. Google raadt aan pas te vergelijken als een update een volle week klaar is, met een week van voor de start.
E. Groeiende onderwerpen: zoekopdrachten waarvan de vertoningen met meer dan 50 procent stegen en die in de laatste periode meer vertoningen hebben dan de mediaan. Groepeer ze in onderwerpen die een blog kunnen worden. De indeling maak je zelf, zonder vaste regel. Zeg dat erbij.
F. Updatelijst: geef elke pagina een punt voor elk signaal. De signalen zijn: staat in lijst B, gedaald in lijst D, genoemd bij vraag 3. Sorteer op punten en daarna op vertoningen. Neem zoveel pagina's als ik bij vraag 4 noemde. Toon per pagina welke signalen meetelden.

Stap 4. De export laat niet zien welke zoekopdracht op welke pagina landt. Vraag me daarom voor de bovenste drie pagina's van lijst F om twee dingen: de tekst van de pagina en een export van de zoekopdrachten van alleen die pagina. Die maak ik in het prestatierapport met een filter op de pagina. Geef daarna per pagina drie concrete wijzigingen. Noem bij elke wijziging de zoekopdracht waar hij bij hoort.

Stap 5. Sluit af met een overzicht dat op één scherm past:
- wat er deze maand gebeurde, in drie zinnen;
- de updatelijst;
- welke cijfers onzeker zijn en waarom.
Geef geen advies dat niet uit een lijst volgt.
```

## Waar het meestal vastloopt

- **Claude vat samen zonder te rekenen.** Zeg: "Reken lijst B uit met code en laat de regel en het aantal rijen zien."
- **De .xlsx wil niet uploaden.** Zet code-uitvoering aan, of exporteer als CSV.
- **Lijst B is leeg.** Kijk in stap 2 hoeveel pagina's zonder match bleven. Verschillen de URL's (met of zonder `www`, met of zonder `/` aan het eind), vraag Claude dan om ze gelijk te maken en opnieuw te koppelen.
