# Hoe maak je met AI een aanmeldpagina die er niet uitziet als AI?

Een prompt die je in ChatGPT of Claude plakt en die je in vijf fases naar een aanmeldpagina voor je gratis weggever brengt. Eerst stelt hij vragen. Dan beslist hij met jou hoe de pagina eruitziet en toetst dat plan tegen twaalf standaardkeuzes van AI. Daarna bouwt en keurt hij. Het formulier komt uit je eigen mailprogramma. Je toetst zelf of een aanmelding aankomt.

**De uitleg stap voor stap:** https://vincentvandeth.nl/blog/aanmeldpagina-zonder-ai-look

## Wat erin zit

| Bestand | Wat het is |
|---|---|
| `prompt.md` | De plak-prompt: vragen, eerste scherm, ontwerpplan, bouwen, keuren en rondes, met een afvinklijst voor je live gaat |
| `keuring.md` | Een prompt die een pagina keurt die al bestaat. Hij verandert niets en geeft de drie wijzigingen die het meeste opleveren |

## Zo gebruik je het

1. Maak eerst in je mailprogramma een insluitformulier en zet de dubbele bevestiging aan. Zet je weggever op de pagina die opent na de klik in de bevestigingsmail, of in een automatische welkomstmail. Niet in de bevestigingsmail zelf: dan krijgt ook een tikfout of een nepadres hem.
2. Plak `prompt.md` in ChatGPT of Claude en beantwoord de zeven vragen.
3. Kies een versie van het eerste scherm en laat de pagina bouwen.
4. Download de letters die de AI noemt van fonts.google.com. Zet ze in een map `fonts` naast de pagina, samen met je foto.
5. Plak de insluitcode van je mailprogramma op de gemarkeerde plek.
6. Zet de map online, of bouw de pagina na in je websitebouwer. Gebruik je Netlify Drop, log dan eerst in of maak een gratis account. Anders staat je pagina achter een tijdelijk wachtwoord. Een nieuw account zet een project standaard op privé: kies daarna dat het openbaar wordt.
7. Loop de afvinklijst onder de prompt na. Meld je aan met twee adressen bij verschillende aanbieders en open de openbare link op je telefoon, zonder ingelogd te zijn.

Heb je al een pagina? Plak dan `keuring.md` in je chat, met de code of een schermafbeelding van je pagina eronder.

Werk je met Claude Code? De ontwerpskill van Anthropic doet het ontwerpdeel goed. Installeer hem en gebruik deze prompt voor de tekst en het formulier:

```
/plugin install frontend-design@claude-plugins-official
```

Zie je zo'n post vaker? Pluis hem zelf uit met de skill [reverse-engineer](../../reverse-engineer/) in deze toolkit. Die doet wat hier gebeurde: hij kiest de vorm en vindt het lastige stuk.

## Wat het niet doet

- Hij maakt geen goede foto en toetst je privacyverklaring niet. Of je de weggever aan je nieuwsbrief mag koppelen, toetst hij ook niet.
- Hij schrijft de mails na de aanmelding niet.
- Hij houdt niet in de gaten of je formulier blijft werken. Meld je na de proefperiode van je mailprogramma opnieuw aan. Doe dat daarna elke maand.

## Licentie

Die van de toolkit. De lijst met kenmerken in beide prompts volgt grotendeels wat Anthropic zelf als standaardkeuzes van AI noemt, in de ontwerpskill `frontend-design` (Apache-2.0) en de blog daarover. Kenmerk 12 is een eigen toevoeging. De tekst is eigen werk.
