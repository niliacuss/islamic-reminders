#!/usr/bin/env python3
"""Send an Islamic reminder to Telegram based on the current Europe/Amsterdam time."""
from __future__ import annotations

import html
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

AMSTERDAM = ZoneInfo("Europe/Amsterdam")
SLOT_HOURS = {10: 0, 15: 1, 20: 2}
REMINDERS_PATH = Path(__file__).parent / "reminders.json"
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def log(msg: str) -> None:
    print(f"[send_reminder] {msg}", flush=True)


def fail(msg: str) -> None:
    log(f"ERROR: {msg}")
    sys.exit(1)


def pick_slot_for_force(hour: int) -> int:
    """When manually triggered, map the current hour to the closest regular slot."""
    if hour < 13:
        return 0
    if hour < 18:
        return 1
    return 2


def main() -> None:
    now = datetime.now(AMSTERDAM)
    log(f"Amsterdam local time: {now.isoformat()}")

    force = os.environ.get("FORCE_SEND") == "1"

    if force:
        slot_index = pick_slot_for_force(now.hour)
        log(f"FORCE_SEND=1 — bypassing hour check, using slot {slot_index}.")
    else:
        slot_index = SLOT_HOURS.get(now.hour)
        if slot_index is None:
            log(
                f"Hour {now.hour} is not a reminder slot (10/15/20). "
                "Exiting cleanly to avoid duplicate sends."
            )
            return

    try:
        reminders = json.loads(REMINDERS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"reminders.json not found at {REMINDERS_PATH}")
    except json.JSONDecodeError as e:
        fail(f"reminders.json is not valid JSON: {e}")

    if not isinstance(reminders, list):
        fail("reminders.json must contain a JSON array.")
    if not reminders:
        fail("reminders.json is empty — add reminder objects before scheduling runs.")

    days_since_epoch = (now.date() - date(1970, 1, 1)).days
    index = ((days_since_epoch * 3) + slot_index) % len(reminders)
    reminder = reminders[index]

    if not isinstance(reminder, dict):
        fail(f"Reminder at index {index} is not an object: {reminder!r}")

    title = (reminder.get("title") or "").strip()
    body = (reminder.get("body") or "").strip()
    if not title or not body:
        fail(f"Reminder at index {index} is missing title or body: {reminder!r}")

    text = f"<b>{html.escape(title)}</b>\n\n{html.escape(body)}"
    log(
        f"Selected reminder index {index} "
        f"(slot {slot_index}, day {days_since_epoch}, total {len(reminders)})."
    )

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token:
        fail("TELEGRAM_BOT_TOKEN environment variable is not set.")
    if not chat_id:
        fail("TELEGRAM_CHAT_ID environment variable is not set.")

    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
    except requests.RequestException as e:
        fail(f"Telegram request failed: {e}")

    if resp.status_code != 200:
        fail(f"Telegram API returned HTTP {resp.status_code}: {resp.text}")

    log("Reminder sent successfully.")


if __name__ == "__main__":
    main()
