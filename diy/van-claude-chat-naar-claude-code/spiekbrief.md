# Spiekbrief: werken in je map `Bedrijf`

Eén pagina voor naast je scherm. De uitleg staat in de blog: https://vincentvandeth.nl/blog/van-claude-chat-naar-claude-code

## Elke keer dat je begint

1. Open de map `Bedrijf` zelf. Nooit een submap: het slot hangt aan deze map.
2. Kijk of de keuzeknop onder het tekstvak op Manual staat.
3. Vraag: wat zijn mijn huisregels? Noemt hij ze niet, zeg dan: lees CLAUDE.md.
4. Zeg wat je wilt, in gewone taal.
5. Lees wat Claude voorstelt voordat je het goedkeurt. Biedt hij aan een commando voortaan niet meer te vragen? Kies dat alleen bij commando's die alleen lezen.
6. Klaar met de taak? Zeg: maak een foto.

## Van de chat naar de map

| In de chat | In je map |
|---|---|
| Een project | Een map onder `projecten` |
| De instructies van het project | `CLAUDE.md` in die map |
| De kennisbestanden | Bestanden in die map, met een lijst in `CLAUDE.md` |
| Wie je bent en hoe je schrijft | `CLAUDE.md` in de hoofdmap, ook te vinden als `AGENTS.md` |
| Een taak die je steeds opnieuw uitlegt | Een skill in `.claude/skills` |
| Je gesprekken | Reken erop dat die in de chat blijven |

## Vier lagen

| Laag | Waar | Wat het is |
|---|---|---|
| Verzoek | `CLAUDE.md` | Tekst die het model leest. Het volgt hem meestal |
| Slot | `.claude/settings.json` | Het programma weigert of vraagt. Het model beslist niet mee |
| Vangnet | Git | Een foto van de map. Daarmee zet je alles terug tot de laatste foto |
| Niet in de map | Een andere plek, liefst niet op deze computer | Wat Claude nooit mag zien. Buiten de map komt hij er niet toevallig langs |

## De vijf standen

| Stand | Wat hij doet |
|---|---|
| Manual | Vraagt voor elke wijziging en bijna elk commando. Lezen doet hij zonder te vragen |
| Accept edits | Bewerkt bestanden zonder te vragen. Verwijdert, verplaatst en kopieert dan ook binnen je map |
| Plan | Maakt een plan en wijzigt niets |
| Auto | Een tweede model beoordeelt elke stap |
| Bypass permissions | Vraagt bijna niets meer. Niet gebruiken in deze map |

## Drie vragen om je slot te toetsen

Doe dit na het inrichten en na elke grote update van de app.

1. Wat zijn mijn huisregels? Hij noemt ze zonder een bestand te openen.
2. Lees prive/proef.txt. Hij zegt dat je instellingen het weigeren. Bestaat het bestand volgens hem niet? Dan klopt de map niet.
3. Voer het commando cat */proef.txt uit. Weiger een vraag waarin unsandboxed staat. De zin uit het proefbestand verschijnt niet.

Verschijnt de zin bij vraag 3? Dan werkt de sandbox op jouw computer niet. Haal dan alles wat privé is uit de map.

Hernoem of verplaats de map `prive` nooit. Het slot hangt aan die naam.

## Eens per maand

- **Een nieuw project.** Zeg: maak een map voor dit project onder projecten, met een CLAUDE.md en een regel onder Waar wat staat.
- **De bestandslijsten.** Zeg: werk de bestandslijst in elk project bij.
- **Het slot.** Stel de drie toetsvragen hierboven opnieuw.

## Als het misgaat

- **Hij doet iets wat je niet wilt.** Klik op stop. Er gebeurt niets meer.
- **Je wilt zien wat er veranderde.** Zeg: laat zien wat er veranderd is sinds de laatste foto.
- **Je wilt terug.** Zeg: zet dit bestand terug naar de laatste foto. Noem het bestand.
- **Hij is de draad kwijt.** Begin een nieuwe sessie en zeg: lees CLAUDE.md.

## Wat waarheen gaat

- Wat je typt en wat Claude opent, gaat naar Anthropic. Wat hij niet opent, blijft op je computer.
- De schakelaar "Help Improve our AI models" onder Privacy bepaalt of je gesprekken voor training gebruikt worden. Die geldt ook hier.
- Git blijft op je computer. Het is een vangnet en geen back-up: het staat op dezelfde schijf.
- Wat op slot zit, staat niet op de foto. Dat back-up je zelf.
