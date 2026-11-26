# Prompt 3: je map leesbaar maken voor een tweede assistent

Plak deze prompt in het tabblad Code van de Claude-app, met je map `Bedrijf` open. Zet de keuzeknop onder het tekstvak op Manual. De prompt stelt vier vragen en wacht op je antwoord. Aan je slot verandert hij niets.

De namen van knoppen en menu's bij OpenAI zijn nagekeken op 26 november 2026. Ze kunnen veranderen.

```text
Je maakt deze map leesbaar voor een tweede AI-assistent, naast Claude. Ik ben geen programmeur en ik ken geen vaktermen. Zeg voor elke stap in één zin wat je gaat doen en waarom, in gewone taal. Gebruik je een vakterm, leg hem dan in dezelfde zin uit. Wijzig niets buiten deze map. Verwijder niets. Vraag nooit om een wachtwoord of sleutel. Verander niets aan .claude/settings.json: dat slot is van Claude en blijft zoals het is.

STAP 1. MIJN SITUATIE
Kijk met een commando welke mappen er in .claude/skills staan. Stel me daarna deze vier vragen in één bericht. Wacht op mijn antwoord voordat je verdergaat.
1. Met welke tweede assistent wil ik deze map ook openen? Deze prompt is geschreven voor Codex van OpenAI.
2. Werk ik op een Mac of op Windows?
3. Welke skills wil ik meenemen? Noem de skills die je vond. Alle of geen mag ook. Neem alleen mee wat ik zelf maakte of zelf gelezen heb.
4. Staat er iets in deze map wat Claude wel mag zien en de tweede leverancier niet?
Weet ik een antwoord niet, ga dan verder met wat je hebt en zeg wat je open liet.
Noem ik een andere assistent dan Codex, zeg dan dat de map voor skills per assistent verschilt. Weet je die map niet zeker, sla stap 4 dan over en zeg dat.

STAP 2. IS DE MAP KLAAR
Kijk met een commando of er in deze map een CLAUDE.md staat. Staat hij er niet, stop dan. Zeg dat ik de map eerst inricht met de uitleg op https://vincentvandeth.nl/blog/van-claude-chat-naar-claude-code. Doe verder niets.
Kijk met een commando of deze map een git-repository is. Zo ja, maak een foto, een commit, met de beschrijving Voor de tweede assistent. Zo nee, zeg dat ik zonder vangnet werk en ga verder.

STAP 3. DE HUISREGELS EEN TWEEDE NAAM GEVEN
CLAUDE.md blijft het echte bestand. AGENTS.md is de naam waaronder Codex zijn regels zoekt.
Kijk met een commando of AGENTS.md bestaat en wat het is: een koppeling naar een ander bestand, of een gewoon bestand. Er zijn vier gevallen.
- Een koppeling naar CLAUDE.md. Dat is goed. Wijzig niets.
- Hij bestaat niet. Maak hem met het commando ln -s CLAUDE.md AGENTS.md. Kijk daarna met een commando of het echt een koppeling is geworden. Op Windows maakt dat commando vaak een kopie. Is het een gewoon bestand, behandel het dan als kopie.
- Een bestand van één regel dat naar CLAUDE.md verwijst. Zeg dat de andere assistent CLAUDE.md dan zelf moet openen en dat niet zeker is of hij dat doet. Raad me een kopie van CLAUDE.md aan en vraag of ik dat wil. Wacht op mijn antwoord.
- Een eigen bestand. Vergelijk het met een commando met CLAUDE.md. Zijn ze gelijk, dan is het een kopie. Verschillen ze, wijzig dan niets. Laat de verschillen zien en zeg dat ik zelf kies wat in CLAUDE.md hoort.

STAP 4. DE SKILLS
Sla deze stap over als ik geen skills koos.
Claude zoekt skills in .claude/skills. Codex zoekt ze in .agents/skills. Het formaat is hetzelfde.
Kopieer de map van elke gekozen skill uit .claude/skills naar .agents/skills, onder dezelfde naam. Verander niets aan het origineel. Maak hier geen koppeling: het slot van deze map houdt dat commando tegen.
Staat er al iets met die naam in .agents/skills, kijk dan met een commando wat het is. Een koppeling naar het origineel is goed: wijzig niets. Een kopie vergelijk je met het origineel. Overschrijf niets zonder het te vragen.
Kijk per skill naar de regels bovenaan SKILL.md, tussen de twee regels met ---. Er horen een name en een description te staan. De name hoort gelijk te zijn aan de naam van de map. Staan er meer velden, noem ze dan en zeg dat niet zeker is of de andere assistent ze kent.

STAP 5. DE AFSPRAKEN VASTLEGGEN
Zet onder het kopje Huisregels in CLAUDE.md de regels die nu gelden. Staat een regel er al, voeg hem dan niet nog eens toe. Laat zien wat je toevoegt.
- Is AGENTS.md een koppeling: De huisregels staan in CLAUDE.md. AGENTS.md is een tweede naam voor hetzelfde bestand. Wijzig altijd CLAUDE.md.
- Is AGENTS.md een kopie: AGENTS.md is een kopie van CLAUDE.md. Wijzig altijd CLAUDE.md en kopieer hem daarna naar AGENTS.md.
- Kopieerde je een skill: Een skill staat op twee plekken. Het origineel staat in .claude/skills, de kopie in .agents/skills. Wijzig het origineel en werk daarna de kopie bij.
Is AGENTS.md een kopie, kopieer CLAUDE.md dan nu opnieuw naar AGENTS.md.
Zeg me wat nu op twee plekken staat en dat die plekken uit elkaar lopen als ik er één met de hand aanpas. Zeg me ook dat ik deze prompt opnieuw plak na een nieuwe skill en anders eens per maand: de controle laat dan zien wat uit elkaar liep.

STAP 6. DE CONTROLE
Tel met commando's en niet op het oog. Laat daarna een tabel zien met per onderdeel waar het staat en of het meereist.
- Huisregels: wat AGENTS.md is, of de inhoud gelijk is aan CLAUDE.md en hoe groot CLAUDE.md is in bytes. Codex leest volgens OpenAI standaard hooguit 32.768 bytes aan instructies bij elkaar. Is het bestand groter, zeg dat dan.
- Projecten: het aantal CLAUDE.md-bestanden onder projecten. Die laadt de andere assistent niet vanzelf. Hij hoort ze te vinden via de regels onder Waar wat staat. Dat is niet getoetst.
- Elke gekozen skill: of het een koppeling of een kopie is. Bij een kopie ook het aantal bestanden in het origineel en in de kopie, en of ze gelijk zijn.
- Vangnet: of git werkt en hoeveel foto's er zijn. De foto's reizen mee: ze staan in deze map.
- Slot: elke regel onder deny en onder ask in .claude/settings.json, mappen en bestanden. Dat reist niet mee. Zeg bij elke regel onder deny dat die map of dat bestand in de andere app niet op slot zit. Zeg bij ask dat de andere app niet vooraf vraagt bij verwijderen en verplaatsen binnen deze map. Staat er geen settings.json, zeg dan dat er geen slot is.
Werkt git, ga dan voor elk pad onder deny en voor alles uit vraag 4 met een commando na of het ooit op een foto stond, zonder het te openen. Stond het op een foto, zeg dan dat weghalen uit de map niet genoeg is: het staat nog in het vangnet en het vangnet reist mee. De eenvoudige route is dan een kopie van deze map zonder de map .git, alleen voor de andere app. Die kopie heeft geen vangnet.
Is een kopie niet gelijk aan het origineel, herstel hem dan alleen als je hem in deze sessie zelf maakte. Bij elk ander verschil laat je het zien en vraag je welke versie geldt.
Werkt git, maak dan een foto met de beschrijving Leesbaar voor een tweede assistent.

STAP 7. WAT IK ZELF DOE IN DE ANDERE APP
Zeg me daarna deze acht dingen, in deze volgorde. Zeg er ook bij dat jij in de andere app niets hebt kunnen toetsen.
1. Het slot geldt alleen in Claude. Wat de andere leverancier niet mag zien, haal ik uit deze map voordat ik hem daar open. De map prive zelf en prive/proef.txt laat ik staan: daarmee toets ik mijn slot.
2. Ik zet bij de andere leverancier eerst de schakelaar voor training uit. Bij OpenAI: Settings, Data controls, Improve the model for everyone.
3. Voordat ik in de andere app werk, laat ik jou een foto maken. Bij Codex is de map .git volgens OpenAI alleen-lezen.
4. Ik open deze map in de andere app.
5. Ik zet de knop voor rechten onder het tekstvak op Ask for approval. In deze map kies ik nooit Full access. Zo heten de standen bij Codex. Dat is een stand voor akkoord en geen slot op een map. De andere app wijzigt binnen deze map zonder te vragen.
6. Ik vraag: wat zijn mijn huisregels? De assistent hoort ze te noemen. Noemt hij ze niet, dan zeg ik: lees AGENTS.md.
7. Koos ik skills, dan vraag ik: welke skills zie je in deze map?
8. Na werk in de andere app vraag ik in Claude opnieuw: lees prive/proef.txt. En ik vraag: laat zien wat er veranderde in .claude, CLAUDE.md en .gitignore.
```
