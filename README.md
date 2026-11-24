# Islamic Reminders

Geautomatiseerd systeem dat dagelijks om **10:00, 13:00, 16:00, 19:00 en 22:00 (Europe/Amsterdam)** een Islamitische reminder naar mijn Telegram stuurt via GitHub Actions.

## Hoe het werkt

- `reminders.json` bevat een array met reminder-objecten (`title` + `body`).
- `send_reminder.py` bepaalt welke reminder gestuurd wordt via een deterministische index:

      ((dagen_sinds_epoch × 5) + slot_index) % totaal_aantal_reminders

  waarbij `slot_index` gelijk is aan `0` voor 10u, `1` voor 13u, `2` voor 16u, `3` voor 19u en `4` voor 22u. Het aantal reminders is een veelvoud van 5, zodat positie `i % 5` altijd hetzelfde tijdslot is. Elke reminder komt één keer aan bod voordat de cyclus zich herhaalt, en de volgorde schuift per dag op zodat je niet altijd dezelfde reminder op hetzelfde tijdstip krijgt.
- De primaire trigger is [cron-job.org](https://cron-job.org): vijf jobs (10:00, 13:00, 16:00, 19:00, 22:00 Europe/Amsterdam) die een `repository_dispatch` naar GitHub sturen. GitHub's eigen cron (4× per uur) is de backup. Het script leidt het slot af uit het Amsterdam-uur (10-12, 13-15, 16-18, 19-21, 22-23) en `.last_sent.json` voorkomt dubbele sends binnen hetzelfde slot.

## Reminders toevoegen

Open `reminders.json` en voeg objecten toe aan de array, bijvoorbeeld:

    [
      {
        "title": "Korte titel",
        "body": "De volledige tekst van de reminder."
      },
      {
        "title": "Volgende reminder",
        "body": "..."
      }
    ]

Commit en push — de volgende cron-run pakt de nieuwe set automatisch op. Het systeem werkt met elk aantal reminders (de modulo zorgt dat de index blijft passen).

## Gedateerde reminders (voorrang op de rotatie)

`reminders_gedateerd.json` koppelt een datum aan vijf berichten (slot 0 t/m 4), elk met `text` (het volledige bericht) en `thema`:

    { "2026-12-01": [ {"text": "...", "thema": "..."}, ... 5 stuks ... ], ... }

Staat de datum van vandaag (Europe/Amsterdam) erin, dan gaat het bericht van het actieve slot als platte tekst naar Telegram. Anders, of als dat bericht onbruikbaar is (ontbreekt, leeg, langer dan 4096 tekens, of met een niet ingevulde `[... invullen]`), geldt de rotatie uit `reminders.json`. Slots, `.last_sent.json` en de dubbel-check werken ongewijzigd: een gemist slot wordt niet ingehaald.

Het bestand wordt gemaakt uit de markdown-bronnen (codeblok per bericht onder een kop `### 12. Dag 3, 13:00`; `### N1.` t/m `### N30.` tellen vanaf 25 november, gewone nummers vanaf 1 december):

    python scripts/maak_gedateerd.py nov.md proefweek.md dec8-19.md dec20-31.md --vereis-volledig

Vooraf bekijken zonder iets te versturen:

    python send_reminder.py --dry-run --date 2026-12-01 --slot 0
    python send_reminder.py --dry-run --date 2026-12-01        # alle vijf slots

## Handmatig triggeren (testen)

1. Ga in GitHub naar **Actions** → **Send Islamic Reminder**.
2. Klik rechtsboven op **Run workflow** → **Run workflow**.
3. Bij een handmatige run wordt de tijdscheck overgeslagen (via `FORCE_SEND=1`), zodat je meteen een bericht ontvangt. Het slot wordt gekozen op basis van het huidige uur.

## Secrets

Zet onder **Settings** → **Secrets and variables** → **Actions**:

- `TELEGRAM_BOT_TOKEN` — bot-token (via [@BotFather](https://t.me/BotFather)).
- `TELEGRAM_CHAT_ID` — je chat ID (bijv. via [@userinfobot](https://t.me/userinfobot)).

## Lokaal testen

    pip install -r requirements.txt
    export TELEGRAM_BOT_TOKEN=...
    export TELEGRAM_CHAT_ID=...
    export FORCE_SEND=1
    python send_reminder.py
