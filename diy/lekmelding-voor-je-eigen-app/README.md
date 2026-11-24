# Zie op tijd of een nieuw lek je eigen app raakt

Voor wie een zelfgebouwde app laat draaien, bijvoorbeeld uit Lovable of gemaakt met Claude. Een geplande taak in GitHub toetst elke ochtend de onderdelen van je app aan de lijst van bekende lekken en aan de lijst van lekken die aanvallers al gebruiken. De uitkomst komt als mail binnen, ook als er niets aan de hand is. Daar zit geen AI in. De plak-prompt maakt van een melding een opdracht voor je bouwtool of je developer.

**Welke apps.** JavaScript en TypeScript (npm, Bun, Yarn, pnpm), Python (pip, Poetry, uv, PDM, Pipfile), Swift (Package Manager), Go, Ruby, Rust, PHP, Java (Maven of Gradle met een `gradle.lockfile`), .NET, Dart en Elixir. Ook R, Haskell en C of C++ met Conan. Die zitten niet in de proefset. Niet: CocoaPods en Gradle zonder `gradle.lockfile`. Voor CocoaPods hebben osv.dev en GitHub geen lekdatabase. Kan Lekcheck niets lezen? Dan zegt hij dat één keer en draait hij daarna stil.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/lekmelding-voor-je-eigen-app

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `lekcheck.yml` | De geplande taak voor GitHub Actions: elke ochtend om 07:30 een reactie onder de issue Lekcheck, die GitHub mailt. Om 13:30, 19:30 en 01:30 alleen een reactie als er iets nieuws is |
| `prompt.md` | De plak-prompt voor Claude of ChatGPT: deel A zet alles op, deel B legt een melding uit |

## Zo zet je de ochtendmail aan

Begin met Dependabot alerts, de bewaking van GitHub zelf: Settings > Advanced Security > Enable bij Dependabot alerts. Gratis en zonder onderhoud. Lekcheck komt erbij voor wat Dependabot niet doet: elke ochtend bewijs dat de bewaking draait, de lijst van CISA en de precieze versies van een app uit Lovable.

Lekcheck zet je zo neer, zonder terminal, op github.com:

1. Staat je app nog niet in GitHub? In Lovable: Project settings > Git > GitHub > Connect.
2. Open de repository van je app. Klik **Add file** > **Create new file**.
3. Typ als naam `.github/workflows/lekcheck.yml`. De schuine strepen maken de mappen vanzelf aan.
4. Plak de inhoud van `lekcheck.yml` en klik **Commit changes**. Zet hem op de standaardbranch: een geplande taak draait alleen daar.
5. Ga naar **Actions** > **Lekcheck** > **Run workflow**. Na de run staat er een issue Lekcheck met de eerste uitkomst.
6. De taak wijst die issue toe aan de eigenaar van de repository. Wie toegewezen is, volgt de issue en krijgt elke reactie per mail. Staat de repository op een organisatie, klik dan zelf **Subscribe** op de issue.

## Instellingen

Bovenaan `lekcheck.yml`, onder `env:`. De standaard past voor de meeste apps.

| Instelling | Wat het doet |
|---|---|
| `LEKCHECK_MELDEN` | `elke-ochtend` (standaard): elke ochtend een reactie, ook als er niets is. `bij-nieuws`: alleen een reactie bij een nieuw of opgelost lek of een storing, en op maandag altijd. Handig als je meerdere apps volgt |
| `LEKCHECK_DIEPTE` | Hoe diep hij naar lock-bestanden zoekt. Standaard acht mappen |
| `LEKCHECK_OVERSLAAN` | Welke mappen hij overslaat. Standaard `node_modules`, `vendor`, `build`, `dist` en een paar andere |
| `LEKCHECK_ISSUE` | Een vast issuenummer, als je de reacties altijd in dezelfde issue wilt |
| `LEKCHECK_OPENBAAR` | `nee` (standaard): op een openbare repository meldt hij niets, want de issue zou je lekken voor iedereen zichtbaar maken. `ja`: toch melden |

De planning staat onder `schedule`. Om 07:30 komt de ochtendreactie. Om 13:30, 19:30 en 01:30 kijkt hij opnieuw en reageert hij alleen bij iets nieuws: een nieuw lek, een lek dat net op de lijst van CISA kwam, of een storing. Wil je dat niet, haal dan de tweede regel `cron` weg. Op een privé-repository kosten vier runs per dag ongeveer zes procent van het gratis tegoed van GitHub Actions.

## Wat de taak doet en mag

- **JavaScript in de hoofdmap.** Een lock-bestand van Bun (`bun.lock` of `bun.lockb`, zoals bij Lovable) gaat voor. Lovable installeert namelijk met Bun. Een `bun.lockb` zet hij eerst om naar `bun.lock`, met dezelfde versies. Zonder Bun-bestand leest hij `package-lock.json` met `npm audit`. Per lek zoekt hij het CVE-nummer op in het advisory van GitHub, ook in de bronnen als het CVE-veld leeg is.
- **Andere talen.** Ook JavaScript in een submap of met Yarn of pnpm. Hij zoekt de lock-bestanden tot acht mappen diep: een app uit Xcode bewaart `Package.resolved` diep in de projectmap. Mappen als `node_modules`, `vendor`, `build` en `dist` slaat hij over. Dat zegt elke reactie. OSV-Scanner van Google leest ze en legt elk onderdeel naast de lekdatabase van osv.dev. Die database komt naar de runner en de vergelijking gebeurt daar. Alleen bij `requirements.txt` en `pom.xml` vraagt OSV-Scanner deps.dev van Google welke onderdelen eronder hangen. Dan gaan de namen en versies van die onderdelen naar Google.
- **Elk lek** legt hij met een vaste regel naast de lijst van CISA, op het CVE-nummer. Die lijst noemt de lekken waarvan bewezen is dat aanvallers ze gebruiken. Een lek dat er niet op staat, kan toch misbruikt worden.
- **Een bestand zonder onderdelen** telt als niet getoetst, nooit als schoon. De reactie noemt het.
- **Versies die niet vastliggen** noemt hij ook. Wat onder een `requirements.txt` of `pom.xml` hangt, rekende deps.dev uit: zo'n versie krijgt "(berekend)". Bij een `requirements.txt` zonder `==` kiest OSV-Scanner zelf een versie. In versie 2.7.1 is dat bij Python soms een oude versie. Dat is niet wat pip zou kiezen. Een onderdeel zonder enige versie toetst hij niet. Dat zegt de reactie. Bij een `.csproj` toetst hij alleen de onderdelen die erin staan, niet wat eronder hangt. Een `package.json`, `pyproject.toml`, `Gemfile` of ander manifest zonder lock-bestand noemt hij als niet getoetst. Een lock-bestand is preciezer.
- **Een kwaadaardig pakket** staat bovenaan, met het advies om het te verwijderen in plaats van bij te werken.
- **Lekken in onderdelen die alleen bij het bouwen draaien**, staan apart. De kop zegt dan "geen bekend lek in de onderdelen van de app zelf" en noemt ze erbij.
- **De vorige keer** onthoudt hij in een verborgen regel in de issue. De kop zegt daardoor hoeveel lekken er nieuw zijn.
- **Hij schrijft alleen in een issue "Lekcheck" die GitHub Actions zelf maakte.** Een issue met dezelfde naam van iemand anders slaat hij over. Twee runs tegelijk kan niet.
- **Tekst van buiten**, zoals namen van onderdelen en titels van lekken, zet hij zo in de reactie dat die de opmaak niet breekt en niemand noemt. Links gaan alleen naar GitHub Advisories en osv.dev. Foutmeldingen staan in de log van de run, niet in de issue.
- **Rechten:** alleen `contents: read` en `issues: write`. Geen geheimen nodig.
- **Vast op één versie:** de actions, Bun (1.4.5) en OSV-Scanner (2.7.1). OSV-Scanner haalt hij alleen op als er een andere taal is. Hij draait hem alleen als de checksum klopt. npm komt mee met de runner van GitHub.
- **Kan hij niets lezen?** Bijvoorbeeld bij CocoaPods. Dan zegt de reactie dat één keer, met het bestand dat hij vond. Daarna draait hij zonder reactie, zonder mail en zonder mislukte run, ook als je de issue sluit. Met een lock-bestand dat hij leest toetst hij vanzelf weer.
- **Lukt de toets zelf niet?** Bijvoorbeeld als `npm audit` of OSV-Scanner geen uitkomst geeft. Dan zegt de reactie dat en mislukt de run. Komt dezelfde storing de volgende dag terug? Dan blijft hij stil tot er iets verandert. Zo krijg je geen dagelijkse foutmail. Dat is een storing en die moet je zien. GitHub meldt een mislukte geplande run aan wie de workflow aanmaakte, of aan wie de regel `cron` daarna wijzigde. Zette je developer het bestand neer? Dan krijgt hij die melding.

## Waar het vastloopt

- **"Lekcheck kan deze app niet toetsen".** De reactie zegt welk bestand hij vond en waarom hij het niet leest. Bij CocoaPods maakt ook GitHub geen lekmeldingen. Bij Gradle: laat de versies vastleggen in een `gradle.lockfile`. Een leeg lock-bestand: zet het actuele lock-bestand in GitHub.
- **Geen mail bij een repository van een organisatie.** De taak wijst de issue toe aan de eigenaar van de repository. Bij een organisatie lukt dat niet. Dan maakt hij de issue zonder toewijzing. Klik dan zelf Subscribe op de issue Lekcheck, anders komt er geen mail.
- **De run mislukt bij "Issue Lekcheck zoeken".** Dan staan Issues uit in de repository. Zet ze aan onder Settings > General > Features > Issues.
- **Geen mail op een ochtend.** Kijk in Actions of de taak gedraaid heeft. Bij drukte op GitHub komt hij later. Een enkele keer valt hij weg.
- **"bun audit gaf geen bruikbare uitkomst".** Gebruikt je bouwtool een nieuwere Bun, zet dan `bun-version` in `lekcheck.yml` op die versie.
- **GitHub noemt een ander aantal dan de reactie.** Dependabot en de toets gebruiken niet precies dezelfde lijst. Dependabot meldt alleen lekken die GitHub zelf beoordeelde. In mijn proef met Next.js 15.2.0 gaf Dependabot 30 meldingen en `npm audit` 48, op hetzelfde lock-bestand.
- **Een openbare repository.** Daar is de issue Lekcheck voor iedereen zichtbaar. Iedereen ziet dan de lekken in je app. Daarom meldt Lekcheck daar niets, tenzij je `LEKCHECK_OPENBAAR` op `ja` zet. Gebruik op een openbare repository liever alleen Dependabot alerts: die ziet alleen de eigenaar. GitHub zet daar bovendien een geplande taak uit na 60 dagen zonder activiteit. Een repository van Lovable is privé.

## Zo gebruik je de prompt

Kopieer het tekstblok uit `prompt.md` en plak het in een nieuw gesprek in Claude of ChatGPT. Beantwoord de vier vragen. Kies A om alles op te zetten, of plak een reactie van Lekcheck of een melding van GitHub voor deel B.

Zelf een skill maken van de prompt? De skill-creator van Claude helpt je een eigen skill op te zetten.

## Wat het niet doet

- Het toetst je eigen instellingen niet: beveiliging per rij in Supabase, sleutels in de browser, functies zonder inlogcontrole. Gebruik daarvoor de scan in Lovable (More > Security) en de Security Advisor van Supabase.
- Het zegt niet of je app door een lek aan te vallen is. En het bewaakt de server en de database zelf niet.
- CocoaPods en Gradle zonder `gradle.lockfile` toetst het niet.
- Getest op GitHub in een privé-testrepository: twee runs, de issue, de toewijzing, de reactie en de mail klopten. De mail komt omdat de issue aan de eigenaar is toegewezen. Kijk de eerste ochtend ook in je spam.
- Het toetst niet de versie van Node.js of Python op je server, geen container-images en niet je eigen code.
- Het kijkt vier keer per dag, niet direct. Wil je bij een kritiek of hoog lek een mail zodra GitHub het publiceert, zet dan ook Dependabot alerts aan.
- Op 24 november 2026 getest met een vaste proefset: per vorm een versie met een bekend lek, in 25 bestanden en 11 talen. Alle 25 gevonden, ook bij een naam met hoofdletters zoals `Sparkle` in Swift. Ook met de regeleinden van Windows. Log4Shell in een `gradle.lockfile` kwam uit de toets met de vermelding dat het op de lijst van CISA staat. Op GitHub getoetst met een Swift-app uit Xcode en een Python-app: vier runs goed.

## Licentie

Die van de toolkit.
