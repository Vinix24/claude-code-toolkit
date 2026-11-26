# Prompt 2: je eerste eigen skill

Gebruik deze prompt na een week, als je weet welke taak steeds terugkomt. Plak hem in de Code-tab, in dezelfde map `Bedrijf`.

```text
Ik wil van een taak die steeds terugkomt een skill maken: een vaste werkwijze die je opnieuw gebruikt zodra die taak terugkomt.

Stel me eerst deze vier vragen in één bericht en wacht op mijn antwoord:
1. Welke taak? Wijs het bestand aan van de laatste keer, of beschrijf wat erin ging en wat eruit kwam.
2. Wat moet elke keer hetzelfde gaan? En wat verschilt per keer?
3. Hoe zie ik dat het goed is? Noem twee of drie toetsen.
4. Wat mag je in deze taak nooit zonder mij doen?

Maak daarna .claude/skills/<naam>/SKILL.md, met een naam in kleine letters en streepjes.
- Bovenaan, tussen twee regels met ---, de velden name en description. De description zegt in één zin wat de skill doet en wanneer je hem gebruikt, met de woorden die ik zelf gebruik als ik erom vraag.
- Daaronder de stappen. Wat vastligt, zoals een lijst, een volgorde of een rekenregel, schrijf je als regel. Alleen het formuleren laat je aan jezelf.
- Als laatste stap de toetsen uit vraag 3. Haalt het resultaat ze niet, zeg dat dan en lever het niet als klaar.
- De regels uit vraag 4 neem je letterlijk over.

Laat me het bestand zien en leg het in vijf zinnen uit. Test de skill daarna op het voorbeeld uit vraag 1 en zet je uitkomst naast wat ik toen maakte. Maak een foto met git als ik tevreden ben.
```

Daarna start je de skill met `/<naam>`, of je vraagt gewoon om de taak. Claude kiest de skill aan de hand van de description.

Een skill is een werkwijze binnen je gesprek. Een subagent is een aparte helper met een eigen geheugen, voor één zijtaak die je gesprek anders zou vullen. Begin met een skill.
