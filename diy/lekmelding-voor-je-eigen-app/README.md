# Zie op tijd of een nieuw lek je eigen app raakt

Voor wie een zelfgebouwde app laat draaien, bijvoorbeeld uit Lovable. Een geplande taak in GitHub toetst elke ochtend de onderdelen van je app aan de lijst van bekende lekken en aan de lijst van lekken die aanvallers al gebruiken. De uitkomst komt als mail binnen, ook als er niets aan de hand is. Daar zit geen AI in. De plak-prompt maakt van een melding een opdracht voor je bouwtool of je developer.

**Alleen voor JavaScript-apps**, met een `package-lock.json`, `bun.lock` of `bun.lockb` in de hoofdmap. Elke app uit Lovable heeft er een. Is je app in Swift, Python of een andere taal? Zet dan Dependabot alerts van GitHub aan. Die kennen veel talen, niet alle. Op zo'n app zegt Lekcheck één keer dat hij niet past. Daarna draait hij stil.

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
- Zonder JavaScript-lock-bestand in de hoofdmap zegt de reactie één keer welke taal hij wel vond. Ook zegt hij of GitHub daar zelf lekmeldingen voor maakt. Hij zoekt tot zes mappen diep: een app uit Xcode bewaart `Package.resolved` diep in de projectmap. De melding onthoudt hij in de tekst van de issue. Daarna draait hij zonder reactie, zonder mail en zonder mislukte run, ook als je de issue sluit. Een lock-bestand in een submap leest hij niet. Dat noemt hij in de melding. Bij een andere taal meldt hij zich opnieuw. Met een lock-bestand dat hij leest toetst hij vanzelf weer.
- Soms lukt de toets zelf niet, bijvoorbeeld als `npm audit` of `bun audit` geen uitkomst geeft. De reactie zegt dat en de run mislukt. Dat is een storing en die moet je zien. GitHub meldt een mislukte geplande run aan wie de workflow aanmaakte, of aan wie de regel `cron` daarna wijzigde. Zette je developer het bestand neer? Dan krijgt hij die melding.

## Waar het vastloopt

- **"Lekcheck past niet bij deze app".** Je app is geen JavaScript-app of gebruikt Yarn of pnpm. Of het lock-bestand staat niet in de hoofdmap. De reactie zegt welke taal hij vond. Maakt GitHub daar zelf lekmeldingen voor, zet dan Dependabot alerts aan: Settings > Advanced Security > Enable bij Dependabot alerts. Kijk daarna bij Insights > Dependency graph of je onderdelen erin staan. GitHub mailt standaard bij een nieuw lek met de ernst kritiek of hoog. Over lekken die er al zijn mailt hij niet: kijk daarvoor één keer in het tabblad Security, bij Dependabot. Vanaf 8 december 2026 zet GitHub Dependabot uit op de meeste repositories zonder activiteit in het afgelopen jaar. Lekcheck mag je dan weghalen: verwijder `.github/workflows/lekcheck.yml`.
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
- Alleen JavaScript-apps met een `package-lock.json`, `bun.lock` of `bun.lockb` in de hoofdmap. Andere talen en `yarn.lock` of `pnpm-lock.yaml` leest hij niet.
- Getest op GitHub in een privé-testrepository: twee runs, de issue, de toewijzing, de reactie en de mail klopten. De mail komt omdat de issue aan de eigenaar is toegewezen. Kijk de eerste ochtend ook in je spam.
- Op 24 november 2026 ook getest met een Swift-app uit Xcode. Eerst één melding dat hij niet past, daarna een stille run. Na een toegevoegd `package-lock.json` volgde weer een gewone toets. GitHub zag de Swift-onderdelen in dezelfde repository via `Package.resolved`.

## Licentie

Die van de toolkit.
