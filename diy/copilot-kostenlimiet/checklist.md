# Checklist: een limiet op Copilot die ook echt begrenst

Voor wie Microsoft 365 Copilot Business heeft. Nagekeken op 12 november 2026. Je hebt geen AI nodig om dit af te vinken. Alles staat in het Microsoft 365-beheercentrum onder **Copilot > Cost management**.

## Vooraf

- [ ] **Weet hoe je koopt.** Kijk wie de afzender is van je factuur: Microsoft zelf of een IT-partner. Bij rechtstreekse aankoop staat betalen per gebruik bij een nieuwe licentie al aan, volgens de melding van Microsoft aan beheerders sinds 19 oktober 2026. Bij een partner is het gepland voor januari tot en met maart 2027.
- [ ] **Regel de juiste rol.** Een nieuwe regel maken kan alleen een globale beheerder of een factuurbeheerder. Een AI-beheerder kan een bestaande regel wel aanpassen.

## In Cost management

- [ ] **Kijk of het aanstaat.** De knop **Get started** betekent: nog niet actief. Een regel op het tabblad **Configuration** betekent: actief.
- [ ] **Bekijk de regel voor alle medewerkers.** De standaard is 4.000 credits per persoon per maand. 100 credits kosten 1 dollar. Dat is tot 40 dollar per persoon. Je betaalt alleen wat echt verbruikt wordt.
- [ ] **Maak die regel niet ruimer dan je teamregels.** Wie in meer regels voor dezelfde dienst staat, krijgt de regel met de hoogste limiet per persoon. Een team op 2.000 naast een regel voor iedereen op 4.000 houdt dus 4.000. Verlaag de regel voor iedereen, of beperk hem tot een groep.
- [ ] **Maak per team een eigen regel.** Via **+ Add spending policy**. Een deel van de medewerkers kies je alleen via een beveiligingsgroep. Maak die groep eerst aan.
- [ ] **Let op het minimum.** Microsoft noemt 2.000 credits per persoon per maand als minimum. Voor alleen apps draaien (Copilot Managed Runtime) raadt Microsoft 100 credits aan. Wil je minder dan het minimum uitgeven, geef een team dan geen toegang.
- [ ] **Kies per regel de diensten.** Credits gaan op aan Cowork, uitgebreid werk in SharePoint en OneDrive, Work IQ API, Copilot Managed Runtime, Teams Phone Agent en Code. Het dagelijkse gebruik van Copilot ("Everyday AI" bij Microsoft) valt onder de licentie.
- [ ] **Zet Auto-apply new services bewust.** Hij staat standaard aan. Dan valt elke nieuwe dienst van Microsoft meteen onder je budget. Zet hem uit als je een nieuwe dienst eerst wilt bekijken.
- [ ] **Zet een melding.** Onder **Define alerts** kies je een drempel in credits of als percentage. De mail komt dagelijks tot het einde van de maand of tot je de regel aanpast. Met een limiet per persoon kun je ook de medewerker zelf een melding geven.
- [ ] **Geef leesrechten.** Wie alleen moet meekijken, zoals iemand van financiën, krijgt de rol **AI Reader** of **Global Reader**. Die ziet het verbruik en kan niets wijzigen.

## Afspraken

- [ ] **Eén functie is eigenaar van de AI-kosten.** Schrijf een functie op, geen naam. Dan blijft het staan als iemand vertrekt.
- [ ] **Begin klein.** Geef eerst één team toegang tot de extra diensten. Breid uit als je na een maand weet wat het kost.

## Elke maand, vijf minuten

- [ ] Open **Consumption** en kies de weergave **Users**. Zie je iemand die hard op zijn limiet afgaat?
- [ ] Kijk op de overzichtspagina van Microsoft of er nieuwe diensten bij zijn gekomen. Met Auto-apply aan vallen ze al onder je budget.

## Koop je via een partner

- [ ] **Vraag je partner wanneer het voor jou aangaat** en welke limieten hij instelt.
- [ ] **Weet dat een nieuwe aankoop het ook aanzet voor licenties die je al hebt.** Eén extra licentie is genoeg.

## Wat deze checklist niet doet

- Hij blijft niet vanzelf actueel. Microsoft verschoof de partnerdatum op 3 november nog van 1 december naar januari tot en met maart 2027.
- Hij rekent niet in euro's. Microsoft noemt de prijs in dollars. Wat het op je factuur wordt, hangt af van je contract.
- Hij zegt niet hoe je het helemaal uitzet. Microsofts eigen pagina's spreken elkaar daarover tegen. Vraag het na bij Microsoft of je partner.

## Bronnen

Alle pagina's geopend op 12 november 2026.

| Wat | Bron |
|---|---|
| Diensten, Auto-apply, Consumption | [Usage-based billing and cost management](https://learn.microsoft.com/en-us/copilot/plan/usage-based-billing-overview-copilot-credits) |
| Get started, rollen, meldingen | [Set up usage-based billing](https://learn.microsoft.com/en-us/copilot/implement/usage-based-billing-copilot-credits-setup) |
| Minimum 2.000, hoogste limiet wint, beveiligingsgroepen | [Managing AI experiences enabled by usage-based billing](https://learn.microsoft.com/en-us/copilot/implement/usage-based-billing-manage-copilot-credits) |
| 100 credits is 1 dollar, 100 credits voor apps draaien | [Manage licensing and Copilot Credits](https://learn.microsoft.com/en-us/microsoft-365/admin/manage/apps/licensing-credits?view=o365-worldwide) |
| Standaard 4.000 per persoon bij een partner, uitzetten | [Usage-based billing in Partner Center](https://learn.microsoft.com/en-us/partner-center/pricing/usage-based-billing-copilot) |
| Partnerdatum januari tot en met maart 2027, bestaande licenties | [Partner Center, aankondigingen november 2026](https://learn.microsoft.com/en-us/partner-center/announcements/2026-november) |
| Het dagelijkse gebruik ("Everyday AI") valt onder de licentie | [Evolution of the Copilot pricing model](https://techcommunity.microsoft.com/blog/microsoft-copilot-blog/evolution-of-the-copilot-pricing-model/4559416) |
| 19 oktober voor rechtstreekse aankoop, standaard 4.000 per persoon bij rechtstreekse aankoop | Melding MC1476200 van Microsoft aan beheerders, 21 september 2026. Die melding is niet openbaar. Gelezen via [lazyadmin.nl](https://lazyadmin.nl/office-365/copilot-business-usage-based-billing/) |
