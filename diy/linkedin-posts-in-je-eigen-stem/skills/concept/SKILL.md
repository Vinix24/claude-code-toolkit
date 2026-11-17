---
name: concept
description: Schrijft een LinkedIn-post bij de opening die de gebruiker koos in 01-haken.md, in zijn stem uit linkedin/stem.md, plus een korte opdracht voor het beeld. Kan de opbouw lenen van een post die de gebruiker goed vond. Verzint geen feiten. Gebruik bij "schrijf de post", "maak het concept", of als tweede stap van /week. Onderdeel van de plugin linkedin-redactie.
---

# Concept: de post en de beeldopdracht

Invoer in de map van de week:

- `01-haken.md`, kopje "Gekozen": de opening, het K-nummer en de pijler
- `notities.md`
- `voorbeeld.md`, als hij bestaat: een post van iemand anders die de gebruiker goed vond
- `linkedin/stem.md`

Staat er niets onder "Gekozen", vraag de gebruiker eerst een opening en een pijler te kiezen. Stop tot hij dat doet.

## Stap 1: de opbouw van het voorbeeld

Alleen als `voorbeeld.md` bestaat. Beschrijf de opbouw in vijf regels:

1. Opening: wat doet de eerste zin?
2. Spanning: welk probleem of welke vraag houdt de lezer vast?
3. Bewijs: waarmee onderbouwt de schrijver het?
4. Wending: waar draait het verhaal?
5. Slot: waar eindigt het?

Zet die vijf regels bovenaan `02-beeld.md` onder het kopje "Opbouw geleend van het voorbeeld". Gebruik in de post alleen die opbouw. Neem geen zin, geen woordgroep en geen voorbeeld uit `voorbeeld.md` over.

## Stap 2: 02-post.md

Schrijf de post. In het bestand staat alleen de posttekst: geen kopjes, geen uitleg.

- De eerste regel is de gekozen opening, zonder het K-nummer en verder ongewijzigd.
- Eén idee. Hooguit 1.300 tekens. Korte alinea's.
- Volg de stemregels uit `stem.md`. Gebruik geen woord uit "Nooit".
- Elk feit, getal, resultaat of verhaal moet terug te vinden zijn in `stem.md`, `notities.md` of een antwoord van de gebruiker in dit gesprek. Kun je het daar niet aanwijzen, verzin het dan niet. Zet `[CHECK: <wat de gebruiker moet aanvullen>]` op die plek.
- Geen naam, bedrijf, mailadres, telefoonnummer of bedrag van een klant.

## Stap 3: 02-beeld.md

Een opdracht voor een beeld, geen beeld:

```markdown
## Beeldopdracht
- Formaat: <vierkant 1:1 of staand 4:5>
- Kop op het beeld: <hooguit zes woorden uit de post>
- Wat er te zien is: <hooguit drie regels>
- Niet op het beeld: namen, bedragen, logo's van klanten
```

## Stap 4: akkoord

Laat de post en de beeldopdracht zien. Noem de stemregels die de post volgt, met hun nummer uit `stem.md`. Noem elke `[CHECK]`.

Vraag om akkoord of wijzigingen. Een wijziging verwerk je in `02-post.md`. Stop tot de gebruiker akkoord geeft.
