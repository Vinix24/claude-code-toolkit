# Zie op tijd of een nieuw lek je eigen app raakt

Voor wie een zelfgebouwde app laat draaien, bijvoorbeeld uit Lovable. Een geplande taak in GitHub toetst elke ochtend de onderdelen van je app aan de lijst van bekende lekken en aan de lijst van lekken die aanvallers al gebruiken. De uitkomst komt als mail binnen, ook als er niets aan de hand is. Daar zit geen AI in. De plak-prompt maakt van een melding een opdracht voor je bouwtool of je developer.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/lekmelding-voor-je-eigen-app

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `lekcheck.yml` | De geplande taak voor GitHub Actions: elke ochtend om 07:30 een reactie onder de issue Lekcheck, die GitHub mailt |
| `prompt.md` | De plak-prompt voor Claude of ChatGPT: deel A zet alles op, deel B legt een melding uit |

## Zo zet je de ochtendmail aan

Zonder terminal, op github.com:

1. Staat je app nog niet in GitHub? In Lovable: Project settings > Git > GitHub > Connect.
2. Open de repository van je app. Klik **Add file** > **Create new file**.
3. Typ als naam `.github/workflows/lekcheck.yml`. De schuine strepen maken de mappen vanzelf aan.
4. Plak de inhoud van `lekcheck.yml` en klik **Commit changes**. Zet hem op de standaardbranch: een geplande taak draait alleen daar.
5. Ga naar **Actions** > **Lekcheck** > **Run workflow**. Na de run staat er een issue Lekcheck met de eerste uitkomst.
6. De taak wijst die issue toe aan de eigenaar van de repository. Wie toegewezen is, volgt de issue en krijgt elke reactie per mail. Staat de repository op een organisatie, klik dan zelf **Subscribe** op de issue.

## Wat de taak doet en mag

- Hij leest het lock-bestand. Een lock-bestand van Bun (`bun.lock` of `bun.lockb`, zoals bij Lovable) gaat voor. Lovable installeert namelijk met Bun. Een `bun.lockb` zet hij eerst om naar `bun.lock`, met dezelfde versies. Zonder Bun-bestand leest hij `package-lock.json` met `npm audit`. Hij installeert niets. De reactie zegt welk bestand hij las.
- Per lek zoekt hij het CVE-nummer op in het advisory van GitHub, ook in de bronnen als het CVE-veld leeg is. Dat nummer legt hij met een vaste regel naast de lijst van CISA.
- Hij onthoudt de lekken van de vorige keer in een verborgen regel in de issue. De kop zegt daardoor hoeveel lekken er nieuw zijn.
- Hij schrijft alleen in een issue "Lekcheck" die hij zelf maakte. Een issue met dezelfde naam van iemand anders slaat hij over.
- Rechten: alleen `contents: read` en `issues: write`. Geen geheimen nodig.
- De actions en Bun (1.4.5) staan vast op één versie. npm komt mee met de runner van GitHub.
- Als de toets niet kan draaien, zegt de reactie dat en mislukt de run. GitHub meldt een mislukte geplande run aan wie de regel `cron` het laatst wijzigde. Zette je developer het bestand neer? Dan krijgt hij die melding.

## Waar het vastloopt

- **Geen mail bij een repository van een organisatie.** De taak wijst de issue toe aan de eigenaar van de repository. Bij een organisatie lukt dat niet. Dan maakt hij de issue zonder toewijzing. Klik dan zelf Subscribe op de issue Lekcheck, anders komt er geen mail.
- **Geen mail op een ochtend.** Kijk in Actions of de taak gedraaid heeft. Bij drukte op GitHub komt hij later. Een enkele keer valt hij weg.
- **"bun audit gaf geen bruikbare uitkomst".** Gebruikt je bouwtool een nieuwere Bun, zet dan `bun-version` in `lekcheck.yml` op die versie.
- **GitHub noemt een ander aantal dan de reactie.** Dependabot en de toets gebruiken niet precies dezelfde lijst. Dependabot meldt alleen lekken die GitHub zelf beoordeelde. In mijn proef met Next.js 15.2.0 gaf Dependabot 30 meldingen en `npm audit` 48, op hetzelfde lock-bestand.
- **Een openbare repository.** Daar zet GitHub een geplande taak uit na 60 dagen zonder activiteit. Een repository van Lovable is privé.

## Zo gebruik je de prompt

Kopieer het tekstblok uit `prompt.md` en plak het in een nieuw gesprek in Claude of ChatGPT. Beantwoord de vier vragen. Kies A om alles op te zetten, of plak een reactie van Lekcheck of een melding van GitHub voor deel B.

Zelf een skill maken van de prompt? De skill-creator van Claude helpt je een eigen skill op te zetten.

## Wat het niet doet

- Het toetst je eigen instellingen niet: beveiliging per rij in Supabase, sleutels in de browser, functies zonder inlogcontrole. Gebruik daarvoor de scan in Lovable (More > Security) en de Security Advisor van Supabase.
- Het zegt niet of je app door een lek aan te vallen is. En het bewaakt de server en de database zelf niet.
- Alleen JavaScript-apps met een `package-lock.json` of `bun.lock` in de hoofdmap.
- Getest op GitHub in een privé-testrepository: twee runs, de issue, de toewijzing, de reactie en de mail klopten. De mail komt omdat de issue aan de eigenaar is toegewezen. Kijk de eerste ochtend ook in je spam.

## Licentie

Die van de toolkit.
