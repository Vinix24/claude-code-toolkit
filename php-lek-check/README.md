# php-lek-check

Een check voor website-eigenaren rond PHP2Shell (CVE-2026-109618 en CVE-2026-109619). Hij leest wat je eigen website laat zien over PHP en maakt een bericht voor je hoster. Hij stelt niet vast of je website kwetsbaar is.

**In het Nederlands.** De check, de uitvoer en het bericht zijn Nederlands.

## Je hebt deze tool waarschijnlijk niet nodig

Ik heb hem in drie versies laten bouwen. Pas daarna stelde ik de vraag die vooraf had gemoeten: moet dit een tool zijn?

Het antwoord is nee, voor bijna iedereen. Of je website kwetsbaar is, weet alleen je hoster. Wat jij moet doen, past in één mail. Stuur je hoster of websitebouwer deze tekst:

```text
Hallo,

Op 21 oktober 2026 verscheen een PHP-update voor PHP2Shell, CVE-2026-109618 en CVE-2026-109619. Ik wil weten of mijn website [je websiteadres] daardoor geraakt kan worden.

Willen jullie drie dingen bevestigen?
1. Wat is de exacte PHP-versie per server achter mijn website?
2. Staat de update van 21 oktober 2026 voor PHP2Shell, CVE-2026-109618 en CVE-2026-109619, op elk van die servers? De reparatie is per reeks PHP 8.2.35, 8.3.36, 8.4.27 of 8.5.12, of een latere versie binnen dezelfde reeks.
3. Zo nee, bevestig de toegepaste backport van de leverancier (een reparatie voor een oudere versie), of geef een datum voor een upgrade naar een ondersteunde reeks.

Graag per server de versie en eventuele backport bevestigen. Alleen WordPress bijwerken lost dit niet op. Bedankt!
```

Je websitebouwer kan het zo zeker weten:

1. **Hostingpaneel** (cPanel, DirectAdmin of Plesk): de volledige PHP-versie per website opzoeken. Staat er alleen 8.3, vraag dan het volledige nummer, zoals 8.3.36.
2. **Tijdelijk versiebestand:** alleen `<?php echo PHP_VERSION;` op de site zetten, openen en direct weer verwijderen. Dat toont de versie achter de site. `php -v` op de opdrachtregel kan een andere versie geven. Een `phpinfo()`-pagina geeft meer prijs dan nodig en mag nooit blijven staan.
3. **De statuspagina of mail van de hoster** over PHP2Shell en beide CVE's.
4. **Debian of Ubuntu:** het changelog of de beveiligingsmelding van het exacte pakket. Laat de leverancier bevestigen dat beide CVE's daarin zijn opgelost.

De versietabel is gecontroleerd op 24 oktober 2026 tegen de primaire PHP-bronnen: [CVE-2026-109618](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w), [CVE-2026-109619](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp) en de [PHP-aankondiging van 21 oktober](https://www.php.net/archive/2026.php). Lees je dit veel later, controleer de nummers dan opnieuw.

## Wat er toch in deze map staat

Voor wie zelf wil kijken, of wil zien wat er gebouwd is:

- **Een Python-script** dat één pagina van je eigen site opvraagt en de zichtbare PHP-signalen beoordeelt. Alleen de standaardbibliotheek, geen installatie.
- **Een Claude-skill** die dat script draait en de uitslag in gewone taal uitlegt.
- **Een losse webpagina** (`index.html`) met een bladwijzerknop en een plakvak. De pagina zelf maakt geen verbinding; een CSP met `connect-src 'none'` dwingt dat af.
- **Tests:** 50 in Python en 75 in JavaScript over dezelfde 70 gevallen, plus een optionele proef in een headless browser.

Wat ik ervan leerde staat in de knop. Een ondernemer die een knop met 25.000 tekens code naar zijn bladwijzerbalk moet slepen, voelt zich alsof hij iets verdachts binnenhaalt. Dat is precies wat beveiligingstrainingen mensen afleren. De mail hierboven heeft dat probleem niet.

Alles over het script, de skill, de pagina en de tests staat in [skills/php-lek-check/README.md](skills/php-lek-check/README.md).

## Installeren als plugin

```
/plugin marketplace add Vinix24/claude-code-toolkit
/plugin install php-lek-check@claude-code-toolkit
```

Of kopieer de map `skills/php-lek-check/` naar `~/.claude/skills/`. Die map is zelfstandig.

## Grenzen

- Alleen voor je eigen site, of met schriftelijke toestemming van de eigenaar.
- Het script en de bladwijzer doen één verzoek naar de opgegeven site. Er gaat niets naar mij, een database of een externe scanner.
- Getest op macOS met Python en Node en in een headless Chromium. Niet getest: gewone Chrome, Edge, Firefox en Safari, Windows en echte telefoons.
- Gebouwd door een AI-codeeragent op mijn opdracht en daarna door een tweede AI-agent getest.
