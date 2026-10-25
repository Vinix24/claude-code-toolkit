# PHP-lek-check

Deze check helpt je de juiste vraag aan je hoster te stellen. Hij stelt niet vast of je website kwetsbaar is.

## Voor ondernemers: de pagina

Open [index.html](index.html) door erop te dubbelklikken. Dit ene bestand werkt op je computer zonder installatie, terminal, Claude, account of API-sleutel. Je kunt het bestand ook los bewaren of doorgeven. Alle code zit erin. Er worden geen lettertypen, afbeeldingen of scripts van buiten geladen.

**Route A:** sleep **Check mijn PHP-versie** naar je bladwijzerbalk, open je eigen website en klik op die bladwijzer. Je krijgt een venster met de uitslag, **Kopieer bericht** en **Sluiten**. Een gewone klik op de knop op de checkpagina toont de leesbare code. Er is ook een manier om de bladwijzer met het toetsenbord aan te maken.

**Route B:** werkt de bladwijzer niet, plak dan de waarde van `X-Powered-By` en vink zo nodig WordPress, Joomla of Drupal aan. Kies **Maak mijn bericht**. Een leeg vak mag ook. Uitleg voor Chrome, Edge, Firefox en Safari staat op de pagina. Bij Safari zet je eerst de functies voor webontwikkelaars aan. Op een telefoon kun je de waarde aan je bouwer vragen, of meteen een bericht maken met een leeg vak. Het websiteadres is niet verplicht en wordt alleen in het bericht gezet.

De pagina zelf doet geen netwerkverzoeken. Je kunt je internet uitzetten en route B blijven gebruiken. De bladwijzer doet op je eigen site één verzoek naar de pagina die je open hebt, leest daarnaast aanwijzingen uit die pagina en volgt geen doorverwijzingen. Hij verstuurt niets naar Vincent, een database of een externe scanner. Een strenge instelling van de site kan de bladwijzer blokkeren. Gebruik dan route B. De pagina is getest in een aparte Chromium-testbrowser; andere browsers en echte telefoons zijn nog niet getest.

Controleer alleen een site waarvan je zelf eigenaar bent of waarvoor je **schriftelijk toestemming** hebt. Zie je iets bij een site van een ander, meld het dan aan de eigenaar en test niet verder.

De check helpt je een vraag te stellen over PHP2Shell: CVE-2026-109618 en CVE-2026-109619. Een WordPress-update lost een lek in PHP zelf niet op. De uitslag bewijst niet of je website kwetsbaar is.

## Met Python gebruiken

Python 3.9 of nieuwer volstaat. Geen pakketten installeren. Open een terminal in de uitgepakte map:

```sh
python3 scripts/check.py "https://jouwsite.nl"
```

Wil je het script los gebruiken, kopieer dan **`scripts/check.py` én `rules.json`** naar dezelfde map en voer daar uit:

```sh
python3 check.py "https://jouwsite.nl"
```

Vervang het voorbeeld door je eigen websiteadres. De aanhalingstekens houden het adres als één argument bij elkaar, ook met `?` of `&`. Het script leest de lokale tabel en haalt daarvoor niets van internet op.

## Wat de uitslag betekent

**PHP aanwezig, versie verborgen** en **Geen PHP gezien** geven allebei geen conclusie over kwetsbaarheid. Stuur het bericht naar je hoster. Een aanwijzing kan ook uit een opgeslagen pagina komen. Geen aanwijzing gevonden betekent niet dat PHP ontbreekt.

| Uitslag | Wat je ermee kunt |
| --- | --- |
| PHP aanwezig, versie verborgen | Onbekend. Het gevonden signaal bewijst niet dat PHP op deze server draait. Vraag de hoster om bevestiging. |
| Geen PHP gezien | Onbekend. Geen aanwijzing gevonden. Dat bewijst niet dat er geen PHP draait. |
| Een oud PHP-nummer is zichtbaar. | Kan kwetsbaar zijn. De header kan van een CDN (een tussendienst), cache (een opgeslagen antwoord) of tussenserver komen. |
| Verouderde PHP met distributie-achtervoegsel | Vanaf 7.4: onbekend. De leverancier kan de reparatie al hebben toegepast. Vraag om bevestiging. |
| Een PHP-versie zonder reparatie van PHP is zichtbaar | Voor 7.3 en ouder, ook 5.x: kan kwetsbaar zijn; PHP zelf noemt voor deze versie geen reparatie, upgrade nodig. Het CDN- en cachevoorbehoud staat direct bij de uitslag. |
| PHP 7.4 tot en met 8.1 | Kan kwetsbaar zijn, tenzij je hoster een backport heeft toegepast. Een backport is een reparatie voor een oudere versie. Vraag om bevestiging, of anders om een upgrade. |
| Het versienummer lijkt bijgewerkt. | Lijkt bijgewerkt volgens het versienummer. De header kan van een andere server komen. Achter één site kunnen meer servers staan. |

Vergelijk per reeks: **8.2.34 kan kwetsbaar zijn, 8.2.35 is de reparatie**. Voor de andere reeksen is de reparatie 8.3.36, 8.4.27 of 8.5.12. Nieuwere versies binnen dezelfde reeks lijken volgens hun nummer ook bijgewerkt. PHP 8.6, andere onbekende reeksen en testversies vallen buiten deze tabel. De tabel is gecontroleerd op **24 oktober 2026**. Het script haalt geen updates voor de tabel op.

Voor **7.4, 8.0 en 8.1** biedt PHP minimale broncode-backports, hoewel deze versies geen gewone updates meer krijgen. De hoster of leverancier moet die code zelf toepassen. Voor **7.3 en ouder, waaronder 5.x**, noemen de geraadpleegde primaire teksten geen broncode-backport. De titel "zonder reparatie van PHP" verwijst naar wat PHP zelf noemt. Een commerciële leverancier kan wel een reparatie hebben. Vraag om een datum voor een upgrade naar een ondersteunde reeks, of om bevestiging van de reparatie van de leverancier. Zie de [PHP-aankondiging van 21 oktober](https://www.php.net/archive/2026.php).

Een distributie-achtervoegsel zoals `-1~deb12u1` maakt een reparatie door de leverancier aannemelijk, maar bewijst die niet. Bij **7.3 en ouder met zo'n achtervoegsel** luidt de beoordeling daarom: **kan kwetsbaar zijn, vraag de leverancier om bevestiging**. Bij een oud nummer vanaf 7.4 met zo'n achtervoegsel blijft de beoordeling **onbekend**.

Zonder achtervoegsel is de volgorde van zwaar naar licht: **7.3 en ouder → 7.4 tot en met 8.1 → een oud nummer in 8.2 tot en met 8.5 → lijkt bijgewerkt**. De oudste groepen krijgen dus geen mildere beoordeling dan een gewone verouderde versie. Bij meerdere PHP-headers gaat de zwaarste aanwijzing voor.

Een zichtbare versie is geen bewijs van de werkelijke installatie. Headers en HTML kunnen uit een opgeslagen pagina of van een tussenserver komen. Een netwerkfout heet **Controle niet afgerond**, met beoordeling **onbekend**. De check doet geen poging het lek te misbruiken.

## Welke signalen worden gelezen?

Bij Python komt alles uit hetzelfde antwoord. De bladwijzer leest dezelfde drie headers uit één nieuw antwoord, en de HTML-signalen uit de al geladen pagina. Hij kan alleen `PHPSESSID` in `document.cookie` zien als die cookie leesbaar is, dus geen HttpOnly-cookies. Route B leest uitsluitend wat je invult. Gevonden links worden niet bezocht.

- De headers `X-Powered-By` en `Server`.
- De cookienaam `PHPSESSID` in `Set-Cookie`. De cookie-waarde wordt niet getoond, bewaard of teruggestuurd.
- Een `Link`-header met `rel="https://api.w.org/"`.
- Een HTML-metatag `generator` die WordPress, Joomla of Drupal noemt.
- HTML-attributen `src`, `action` of `href` met `.php`, `/wp-content/`, `/wp-includes/`, `/wp-json/` of `index.php?`.

De uitvoer noemt welke signalen zijn gevonden. Alleen `PHP/major.minor.patch` in `X-Powered-By` of `Server` wordt als PHP-versie vergeleken. De andere signalen leiden hoogstens tot **PHP aanwezig, versie verborgen**. Een aangepaste of onherkenbare `X-Powered-By` zonder PHP-nummer is een zwak signaal: het kan ook een andere techniek zijn. Een CMS-versie of `?ver=`-nummer is nooit een PHP-versie.

Het bericht aan de hoster vraagt drie dingen: de exacte PHP-versie per server achter je site, of de update van 21 oktober erop staat en, zo nee, om bevestiging van de toegepaste backport van de leverancier, of een datum voor een upgrade naar een ondersteunde reeks. Het noemt beide CVE's en de reparatie per reeks.

## Op Windows

Installeer Python via [python.org](https://www.python.org/downloads/windows/) of de Microsoft Store. Kopieer `scripts/check.py` en `rules.json` samen naar een map en open daar een terminal:

```powershell
py check.py https://jouwsite.nl
```

Gebruik **dubbele aanhalingstekens**, vooral bij adressen met `?` of `&`:

```powershell
py check.py "https://jouwsite.nl/?pagina=1&taal=nl"
```

Werk je vanuit de uitgepakte skillmap, gebruik dan `py scripts/check.py "https://jouwsite.nl"`. De handmatige route is:

```powershell
curl.exe -sI https://jouwsite.nl | findstr /i "x-powered-by server"
```

In PowerShell moet het echt **`curl.exe`** zijn. Dit leest alleen headers en volgt geen redirects. **Niet getest op Windows.**

## Wat er met je gegevens gebeurt

Je websiteadres gaat niet naar mij en niet naar een database. Gebruik je de check via Claude, dan staan het adres en de uitslag in je eigen Claude-gesprek. Wil je dat ook niet, open dan de lokale pagina of draai het script los.

Met "mij" bedoel ik Vincent, de maker. Het losse script draait op je computer. In de Claude-app kan het in de omgeving van Claude draaien. Gebruik de lokale route hierboven als je het adres en de uitslag buiten Claude wilt houden.

De code is open te lezen in [index.html](index.html), [src/](src/) en [scripts/check.py](scripts/check.py). Je kunt zelf zien dat er geen adres naar mij, een database of een externe scanner wordt verstuurd. Het opgegeven adres wordt wel gebruikt om je eigen site te bereiken.

De check is gebouwd door een AI-codeeragent op Vincents opdracht en daarna door een tweede AI-agent getest.

Het script gebruikt alleen de Python-standaardbibliotheek. Het schrijft geen bestanden en maakt geen log of cache. Het bevat geen telemetrie, update-check of koppeling met een externe scanner. Een netwerkproxy uit omgevingsvariabelen wordt niet gebruikt. Het besturingssysteem zoekt het IP-adres van de opgegeven host op zoals bij ander websitebezoek.

Het script vraagt één pagina op met GET en volgt maximaal vijf doorverwijzingen op dezelfde host en poort. Van http naar https op de standaardpoorten mag wel. Doorverwijzingen naar een andere host, ook een `www`-variant, worden gestopt. Voer dan zelf het juiste uiteindelijke adres in. De time-out is 15 seconden per netwerkhandeling. Alleen de eerste 1 MiB HTML wordt beoordeeld; een afkapping wordt gemeld. Afbeeldingen en scripts worden niet geladen.

## In Claude gebruiken

### Claude Code

Installeer de plugin uit deze marketplace, of kopieer deze map naar `~/.claude/skills/`. In het tweede geval moet dit bestand bestaan:

```text
~/.claude/skills/php-lek-check/SKILL.md
```

Vraag daarna bijvoorbeeld: "Controleer mijn website https://jouwsite.nl op het PHP-lek."

### Claude-app

Maak eerst een zip van deze map, zonder de tests:

```sh
cd claude-code-toolkit/php-lek-check/skills
zip -r php-lek-check.zip php-lek-check -x 'php-lek-check/tests/*' 'php-lek-check/output/*'
```

Op 23 oktober 2026 is de uploadroute bekeken in de aangemelde Claude-desktopapp, versie **3.6556.2**:

1. Open **Claude > Settings…**.
2. Kies in de zijbalk onder **Customize** de optie **Skills**. Scroll de zijbalk zo nodig omlaag.
3. Kies rechtsboven **+ Add > Upload skill**.
4. Kies `php-lek-check.zip` en klik op **Upload**.

Het geopende scherm **Upload a skill** bevestigt dat een `.zip` een `SKILL.md` moet bevatten. Het scherm vermeldt ook dat Claude bij uploaden een controle uitvoert.

De op 23 oktober geraadpleegde [Claude-handleiding](https://support.claude.com/en/articles/12512180-use-skills-in-claude) noemt voor de webinterface **Customize > Skills > + > Create skill > Upload a skill**. De knopnamen verschillen dus per interface. **Code execution and file creation** moet aanstaan bij **Settings > Capabilities**. Dit zijn eerdere waarnemingen uit v1. De app is voor v3 niet bediend; de actuele uploadroute is niet opnieuw getest.

### Geen internet in Claude

Gebruik de lokale pagina, of draai het script op je eigen computer. Voor Chrome, Edge en Firefox op een computer kun je ook de website openen, druk F12, kies **Netwerk**, herlaad de pagina en klik het eerste verzoek aan. Kijk bij **Response Headers** naar `X-Powered-By` en `Server`.

In een terminal kan ook:

```sh
curl -sI https://jouwsite.nl | grep -i -e x-powered-by -e server
```

Dit handmatige commando leest alleen de twee genoemde headers en volgt geen redirects. Het kijkt niet naar de extra signalen die het script gebruikt. Geen PHP-header gevonden betekent dat de versie onbekend blijft.

## Voor wie de uitvoer wil verwerken

```sh
python3 scripts/check.py "https://jouwsite.nl" --json
```

`uitkomst` is `verborgen`, `geen_php`, `verouderd`, `distributie`, `oud` of `bijgewerkt`. De zes bestaande codes zijn behouden. Binnen `oud` verschillen titel en beoordeling voor 7.3 en ouder en 7.4 tot en met 8.1. Een achtervoegsel bij 7.3 en ouder geeft binnen `oud` een eigen beoordeling; bij oude versies vanaf 7.4 leidt het tot `distributie`. De JSON begint met `doel` en bevat ook de beoordeling, eventuele PHP-versie, `vergelijking`, `aanwijzingen.signalen` en `bericht_hoster`. `--json` schrijft één JSON-object, zonder tekst ervoor.

Afsluitcode 0 betekent dat de meting is afgerond, ongeacht de beoordeling. Afsluitcode 2 en `uitkomst: null` betekenen dat geen volledige beoordeling mogelijk was. Gebruik een fout dus nooit als bewijs dat PHP ontbreekt.

## Voor je websitebouwer: zo weet je het zeker

Deze stappen staan ook op de pagina en onder ieder gekopieerd bericht. Alleen de beheerder met toegang en toestemming voert ze uit; de check plaatst zelf geen bestanden.

1. Hostingpaneel (cPanel, DirectAdmin of Plesk): controleer de volledige PHP-versie per website. Bij alleen 8.3: vraag het volledige nummer, zoals 8.3.36.

2. Tijdelijk versiebestand: plaats alleen `<?php echo PHP_VERSION;` op de site, open het en verwijder het bestand direct. Dit toont de PHP-versie achter de site. `php -v` op de opdrachtregel kan een andere versie tonen. Een `phpinfo()`-pagina geeft meer prijs dan nodig is en mag nooit blijven staan.

3. Controleer de statuspagina of mail van de hoster over PHP2Shell, CVE-2026-109618 en CVE-2026-109619.

4. Debian of Ubuntu: controleer het changelog (de wijzigingenlijst) of de melding over de reparatie van het exacte pakket. Laat de leverancier bevestigen of beide CVE’s daarin zijn opgelost.

## Eén bron, drie uitvoervormen

[rules.json](rules.json) is de enige onderhouden bron voor de versietabel, de geordende beoordelingsregels, de beoordelingen, de signalen en het hosterbericht. Python leest dit bestand. [src/core.js](src/core.js) voert dezelfde regels uit voor de pagina en de bladwijzer. Beiden gebruiken [src/render.js](src/render.js) om de uitslag en het bericht te tonen.

[scripts/build.py](scripts/build.py) zet de tabel en de JavaScript-code in `index.html`, zonder externe bestanden nodig te hebben tijdens gebruik. Bewerk de bronnen in `src/` of `rules.json`, en bouw daarna opnieuw:

```sh
python3 -B scripts/build.py
python3 -B scripts/build.py --check
```

De tweede opdracht controleert dat het HTML-bestand precies bij de bronnen hoort. Pas `index.html` niet met de hand aan. De bladwijzerbron is ook op de pagina leesbaar via **Met het toetsenbord gebruiken of de code lezen**.

## Tests

Python 3.9+ en Node 18+ zijn nodig voor de gezamenlijke tests. Geen npm-pakketten:

```sh
python3 -B -m unittest discover -s tests -v
node --test tests/check.test.cjs
```

Beide draaien dezelfde **70 gevallen** uit [cases.json](cases.json). Python vergelijkt bovendien de volledige resultaten uit beide talen, inclusief het hosterbericht. De voorbeelden omvatten alle patchgrenzen, oude versies, distributie-achtervoegsels, tegenstrijdige headers, cookies, CMS-signalen en versienummers die geen PHP zijn. De volgordetest vergelijkt de werkelijk uitgegeven beoordeling. Bij meerdere headers wint de zwaarste aanwijzing.

De tests bewijzen per taal dat een verandering van de grens `8.4.27` naar `8.4.26` wordt afgekeurd. Ook een oude versie die ten onrechte alleen "onbekend" krijgt, wordt afgekeurd. De Python-tests controleren daarnaast netwerkfouten, redirects, de CLI en JSON. De privacytest leest het HTML-bestand en weigert externe bronnen buiten de bronnenlijst, CSS-imports en `url(...)`, netwerkcode buiten de bladwijzer en een ontbrekende CSP. Opzettelijke overtredingen laten die test falen.

**Controle v3 op 24 oktober 2026:** 50 Python-tests en 75 JavaScript-tests slagen. Het script telt 175 regels.

### Optionele headless browserproef

Node 22+ en een apart geïnstalleerde Chromium-testbinary zijn nodig, zonder npm-pakketten. Gebruik geen bestaande browser of bestaand gebruikersprofiel:

```sh
PHP_CHECK_CHROMIUM="/pad/naar/chrome-headless-shell" node tests/headless.cjs
```

Deze proef maakt zelf een tijdelijk profiel en een testserver op `127.0.0.1`. Zij controleert offline gebruik via `file://`, alle 70 gevallen in de echte DOM, kopiëren met een testdubbel voor het klembord, toetsenbordfocus, een breedte van 375 pixels en de bladwijzer als echte `javascript:`-link. Zij controleert ook één GET, geen gevolgde doorverwijzing, blokkering bij strenge site-instellingen en herstel van de pagina na Sluiten. Het tijdelijke profiel wordt verwijderd. Testbeelden en een verslag komen in `output/headless/`; die map staat in `.gitignore`.

De proef slaagt in **HeadlessChrome 153.0.8010.12 op macOS**. Het echte browserprofiel, systeemklembord en de Claude-app zijn niet gebruikt. Niet getest: normale Chrome, Edge, Firefox, Safari, Windows, Android, iOS, fysieke telefoons en slepen naar de bladwijzerbalk. De smalle weergave is een simulatie. Een browser of site kan de bladwijzer blokkeren. Een geslaagde test met een klembord-testdubbel bewijst geen klembordtoestemming in iedere browser.

## Stap 0: feiten en bronnen

Op 24 oktober 2026 zijn beide primaire PHP-advisories en de PHP-aankondiging van 21 oktober opnieuw gelezen. De versietabel komt uit deze bronnen:

- [CVE-2026-109618: PHP-advisory](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)
- [CVE-2026-109619: PHP-advisory](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp)
- [PHP-aankondiging van 21 oktober 2026](https://www.php.net/archive/2026.php)

De lekken zijn ernstig. De advisories beschrijven geslaagde demonstraties van uitvoering van code op afstand. Een update met de reparaties is de enige volledige oplossing voor deze twee lekken. Deze check voert zulke demonstraties niet uit. Zie [GHSA-w8hw-w9fx-j79w](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w) en [GHSA-6wmf-4rv5-p3rp](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp).

PHP noemt PHP-FPM, Apache met mod_php, php-cgi, FrankenPHP en LiteSpeed als betrokken manieren om PHP aan een webserver te koppelen. PHP schat het risico bij mod_php het hoogst in. De voorwaarden en aangetoonde aanvalsroutes verschillen per lek en koppeling. De check stelt die koppeling niet vast. De [PHP-aankondiging](https://www.php.net/archive/2026.php) bevestigt ook de broncode-backports voor 7.4, 8.0 en 8.1 en de rol van distributies en leveranciers.

**Niet als feiten overgenomen:** dat er een publiek beschikbare proof-of-concept is, dat Sophos pogingen en één geslaagde aanval zag, dat Sansec minder massamisbruik verwacht, of dat voor 7.3 en ouder nergens een fix bestaat. De geraadpleegde primaire teksten dragen die uitspraken niet. Dat is geen bewijs dat ze onjuist zijn. De aantoonbare demonstraties worden wel vermeld; uitspraken over werkelijk misbruik worden niet afgeleid uit een versienummer.
