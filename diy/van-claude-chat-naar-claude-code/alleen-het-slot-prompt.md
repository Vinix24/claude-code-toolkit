# Alleen het slot

Voor wie al een map heeft waarin Claude werkt en alleen het slot wil. Plak deze prompt in het tabblad Code van de Claude-app, met die map open. Zet de keuzeknop onder het tekstvak op Manual.

```text
Zet in deze map alleen het slot neer. Ik ben geen programmeur en ik ken geen vaktermen. Zeg voor elke stap in één zin wat je gaat doen en waarom, in gewone taal. Gebruik je een vakterm, leg hem dan in dezelfde zin uit. Wijzig niets buiten deze map. Verwijder niets.

1. Kijk met een commando in welke map je staat. Is dit mijn thuismap, Documenten, Bureaublad of Downloads? Stop dan en zeg dat ik een eigen map moet openen.
2. Kijk met git --version of git werkt. Verschijnt op een Mac een venster van Apple dat hulpmiddelen wil installeren, stop dan. Wacht tot ik zeg dat de installatie klaar is en kijk opnieuw. Werkt git en is deze map nog geen git-repository, maak er dan een van. Zet prive/, .env en .env.* in .gitignore. Heeft git nog geen naam en mailadres, stel dan alleen voor deze map de naam Ik en het mailadres ik@lokaal in. Maak een foto, een commit, met de beschrijving Voor het slot. Doe dit voor het slot: met het slot erop kan git niet meer worden opgezet.
3. Maak de map prive met daarin het bestand proef.txt, met de zin: Als je dit leest, werkt het slot niet.
4. Maak .claude/settings.json met precies deze inhoud. Ik krijg daarvoor een vraag om akkoord en keur die goed. Bestaat het bestand al, voeg dan alleen toe wat ontbreekt en haal niets weg. Staat er al een andere waarde voor een instelling uit dit blok, laat dan beide zien en vraag welke blijft.
{
  "permissions": {
    "defaultMode": "default",
    "blockReadsOutsideWorkingDirectories": true,
    "deny": [
      "Read(./prive/**)",
      "Read(./.env)",
      "Read(./.env.*)"
    ],
    "ask": [
      "Bash(rm *)",
      "Bash(mv *)",
      "Bash(curl *)",
      "Bash(git push *)",
      "Bash(git reset *)",
      "Bash(git clean *)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": false,
    "allowUnsandboxedCommands": false
  }
}
Wordt het schrijven geweigerd, geef me dan geen commando's voor een terminal. Zeg dat het slot er niet op zit.
5. Maak een foto met de beschrijving Slot erop. Zeg me daarna dat ik in een nieuwe sessie drie dingen vraag:
- Lees prive/proef.txt. Je hoort te zeggen dat mijn instellingen het weigeren.
- Voer het commando cat */proef.txt uit. De zin uit het proefbestand mag niet verschijnen. Vraag je of het commando buiten de sandbox mag, dan weiger ik dat.
- Verschijnt de zin toch, dan werkt de sandbox op mijn computer niet. Dan haal ik alles wat privé is uit deze map.
Zeg er ook bij: open altijd deze map zelf en nooit een submap, en hernoem of verplaats de map prive nooit.
```
