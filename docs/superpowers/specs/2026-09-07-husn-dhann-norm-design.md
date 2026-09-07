# Husn adh-Dhann norm en herbouw van de reminders

Datum: 2026-09-07. Besluit van Fouad: optie B, volledige herbouw van `reminders.json`.

## Doel

Elke reminder helpt Fouad het goede over Allaah te denken (husn adh-dhann), zodat hij niet
wanhopig wordt en niet overmand raakt door zonden, problemen of zorgen. Inspirerend en
motiverend, geen algemene aanmoediging, geen praktijkles, geen beloningsrekensom.

## De norm (elke reminder, zonder uitzondering)

1. Begint bij jou: een zin die een herkenbare staat benoemt (de zonde die knaagt, de zorg die
   wakker houdt, het gevoel vergeten te zijn).
2. De kern is een waarheid over Allaah (vers, authentieke hadith of naam van Allaah) die die
   staat weerlegt. Geen instructie als kern.
3. De draai staat letterlijk in de tekst: "zo mag je over Hem denken: ..." (of een even
   expliciete variant). Dit is het hart, niet een slotformule.
4. Het slot tilt op: hoop en rust, hooguit een kleine, zachte uitnodiging. Geen to-do-lijst.
5. Verboden als hoofdinhoud: "wie X doet krijgt Y", levensadvies, neutrale verhalen, uitleg
   van een naam zonder troost, vermaning.

Vorm blijft gelijk: titel met sparkles, body met gedachtewolk, 250 tot 400 tekens, geen
gedachtestreepjes of aanhalingstekens, honorifieken en spellingen zoals in de bestaande set.

## Dagstructuur: drie fronten

`send_reminder.py` kiest index `(dagen_sinds_1970 * 3 + slot) % len`. Zolang `len`
deelbaar is door 3, krijgt slot 0 altijd posities 0, 3, 6, ..., slot 1 posities 1, 4, 7, ...
en slot 2 posities 2, 5, 8, .... Daarom wordt de set zo opgebouwd:

- positie 0 mod 3 (10:00): tegen zorgen en problemen (Hij beheert wat jij niet beheert)
- positie 1 mod 3 (15:00): tegen zonden en schuld (Hij vergeeft ruimer dan jij jezelf)
- positie 2 mod 3 (20:00): tegen wanhoop en moedeloosheid (Hij is niet klaar met jou)

Binnen elk front roteren sub-invalshoeken (bijv. zorgen: voorziening, gezondheid, kinderen,
toekomst, werk, angst; zonden: herhaalde zonde, schaamte, grote zonde, onwaardig voelen,
angst voor straf, verleden; wanhoop: onverhoorde du'a, lange beproeving, eenzaamheid,
vergeten voelen, zwakte, vermoeidheid) zodat opeenvolgende dagen niet op elkaar lijken.

## Omvang en uitrol

- Doel: 441 reminders = 147 dagen = 7 september 2026 t/m 31 januari 2027 (maandregel: elke
  volgende batch vult exact tot het einde van de volgende maand).
- Eerst 9 voorbeelden (drie dagen) ter goedkeuring in de chat.
- Daarna in blokken van 90 (30 dagen). Na goedkeuring van blok 1 gaat dat blok direct live
  ter vervanging van de huidige set; volgende blokken worden aangehecht tot 441.
- De huidige 441 worden bewaard in `archive/husn_dhann_v1_441.json` (git-historie `c780c19`).

## Kwaliteitspoort per blok

1. Automatisch: lengte, vorm, geen dubbele titels, Jaccard-overlap onder 0,40 (intern en
   tegen alle eerder goedgekeurde blokken), front per positie klopt, elke body bevat de
   expliciete draai.
2. Onafhankelijke beoordeling: een Opus-subagent scoort elke reminder 1 tot 5 op elk van de
   vijf normpunten. Alles met een score onder 4 op enig punt wordt herschreven en opnieuw
   beoordeeld.
3. Steekproef in de chat bij elk blok: drie dagen laten zien voordat het blok live gaat.

## Bronnen

Alleen Quraan en authentieke overleveringen (Bukhari, Muslim, en hasan-overleveringen met
zachte attributie "wordt overgeleverd"). Geen Ramadan, zakaah of hajj als thema, geen
tafsir-uitleg van verzen, geen fabricaties.
