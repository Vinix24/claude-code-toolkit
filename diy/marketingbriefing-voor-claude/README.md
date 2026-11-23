# Hoe laat je Claude je bedrijf kennen voor marketingwerk?

Een Nederlandse prompt die een marketingbriefing voor je bedrijf schrijft, met de woorden van je eigen klanten. Het bestand volgt de opbouw van de open-source marketingskills op GitHub (53 skills, MIT-licentie). Die skills lezen de briefing voordat ze een taak doen. Zonder skills werkt de briefing ook: als bestand in een Claude- of ChatGPT-project.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/marketingbriefing-voor-claude

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `briefing-prompt.md` | De prompt. Hij vraagt eerst naar je situatie en om vijf echte stukken, en schrijft daarna de briefing |
| `README.md` | Dit bestand: de startset van acht skills en hoe je ze installeert |

## Zo gebruik je het

**Alleen de briefing.** Plak `briefing-prompt.md` in Claude of ChatGPT. Bewaar het resultaat als bestand in een project. Elk gesprek in dat project kan het dan gebruiken.

**Met de skills.** Installeer de startset in de map van je bedrijf. De installer vraagt Node.js 22.20 of nieuwer.

```bash
npx skills add coreyhaines31/marketingskills -a claude-code --skill product-marketing customer-research copywriting copy-editing social emails content-strategy seo-audit
```

De installer verzamelt anonieme gebruiksgegevens. Zet `DISABLE_TELEMETRY=1` voor het commando om dat uit te zetten.

Bewaar daarna de briefing als `.agents/product-marketing.md` in dezelfde map. Of laat de skill `/product-marketing` hem maken.

| Skill | Waarvoor |
|---|---|
| `product-marketing` | Maakt en onderhoudt de briefing. Zonder briefingbestand vragen de anderen alles opnieuw |
| `customer-research` | Haalt patronen uit interviews, enquêtes, supportgesprekken en reviews |
| `copywriting` | Teksten voor je homepage en landingspagina's |
| `copy-editing` | Bestaande tekst aanscherpen zonder hem te herschrijven |
| `social` | Posts voor LinkedIn en andere kanalen |
| `emails` | Mailreeksen, zoals een welkomstreeks |
| `content-strategy` | Waar je over schrijft en in welke volgorde |
| `seo-audit` | Waarom een pagina niet gevonden wordt |

Een deel van de 53 skills is geschreven voor softwarebedrijven: paywalls, aanmeldflows, app-stores, opzeggingen. Die laat je weg tot je ze nodig hebt. Hoe minder skills, hoe korter de lijst waaruit Claude kiest.

Zelf een skill maken die dezelfde briefing leest? Laat de skill-creator van Claude hem opzetten. Zet als eerste instructie: "Lees eerst `.agents/product-marketing.md`."

## Wat het niet doet

- Een skill doet niets tot je hem iets vraagt.
- De prompt verzint geen klantkennis. Wat ontbreekt, markeert hij.
- Wat je plakt, gaat naar de AI-leverancier van je assistent. Haal namen en bedragen eruit.
- In een project staat de briefing bij de leverancier van dat project. Met de skills staat hij op je eigen computer.

## Licentie

MIT, net als de rest van deze toolkit. De marketingskills zelf staan niet in deze map. Die haal je bij de bron, onder hun eigen MIT-licentie.
