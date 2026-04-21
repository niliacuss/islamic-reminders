# Islamic Reminders

Geautomatiseerd systeem dat dagelijks om **10:00, 15:00 en 20:00 (Europe/Amsterdam)** een Islamitische reminder naar mijn Telegram stuurt via GitHub Actions.

## Hoe het werkt

- `reminders.json` bevat een array met reminder-objecten (`title` + `body`).
- `send_reminder.py` bepaalt welke reminder gestuurd wordt via een deterministische index:

      ((dagen_sinds_epoch × 3) + slot_index) % totaal_aantal_reminders

  waarbij `slot_index` gelijk is aan `0` voor 10u, `1` voor 15u en `2` voor 20u. Elke reminder komt één keer aan bod voordat de cyclus zich herhaalt, en de volgorde schuift per dag op zodat je niet altijd dezelfde reminder op hetzelfde tijdstip krijgt.
- GitHub Actions triggert via cron op 10, 15 en 20 uur Amsterdam-tijd. Omdat Amsterdam zomer- en wintertijd heeft staan er **6 cron-entries** (3 voor CET, 3 voor CEST). Het script controleert zelf of de huidige Amsterdam-tijd daadwerkelijk 10/15/20 uur is en exit anders zonder te versturen — dit voorkomt dubbele sends rondom DST.

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
