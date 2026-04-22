#!/usr/bin/env python3
"""Send an Islamic reminder to Telegram based on the current Europe/Amsterdam time.

Slot windows (tolerant of GitHub Actions cron delays):
- Hour 10-14  -> slot 0 (10u reminder)
- Hour 15-19  -> slot 1 (15u reminder)
- Hour 20-23  -> slot 2 (20u reminder)
- Hour 0-9    -> skip (pre-morning window)

A state file (.last_sent.json) records the last (date, slot) that was delivered,
so if GitHub Actions fires twice within the same slot window the second run skips
instead of resending.

FORCE_SEND=1 bypasses both the window check and the state file check, and
deliberately does NOT update the state file (so manual tests do not interfere
with the scheduled rotation).
"""
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
SCRIPT_DIR = Path(__file__).parent
REMINDERS_PATH = SCRIPT_DIR / "reminders.json"
STATE_PATH = SCRIPT_DIR / ".last_sent.json"
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def log(msg: str) -> None:
    print(f"[send_reminder] {msg}", flush=True)


def fail(msg: str) -> None:
    log(f"ERROR: {msg}")
    sys.exit(1)


def slot_for_hour(hour: int) -> int | None:
    """Return the active slot for an Amsterdam hour, or None if outside the window."""
    if 10 <= hour <= 14:
        return 0
    if 15 <= hour <= 19:
        return 1
    if 20 <= hour <= 23:
        return 2
    return None


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log(f"Warning: could not read {STATE_PATH.name} ({e}); treating as empty.")
        return {}


def save_state(today_iso: str, slot: int) -> None:
    payload = {"date": today_iso, "slot": slot}
    STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log(f"State file updated: date={today_iso} slot={slot}")


def main() -> None:
    now = datetime.now(AMSTERDAM)
    log(f"Amsterdam local time: {now.isoformat()}")

    force = os.environ.get("FORCE_SEND") == "1"

    slot_index = slot_for_hour(now.hour)
    if slot_index is None:
        if force:
            slot_index = 0
            log(
                f"FORCE_SEND=1 — hour {now.hour} is outside the active window "
                "(10-23); defaulting to slot 0."
            )
        else:
            log(
                f"Hour {now.hour} is outside the active window (10-23). "
                "Exiting cleanly."
            )
            return

    today_iso = now.date().isoformat()

    if force:
        log("FORCE_SEND=1 — skipping state file check, will not update state.")
    else:
        state = load_state()
        if state.get("date") == today_iso and state.get("slot") == slot_index:
            log(
                f"Slot {slot_index} for {today_iso} was already sent "
                f"(per {STATE_PATH.name}). Exiting cleanly."
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

    if not force:
        save_state(today_iso, slot_index)


if __name__ == "__main__":
    main()
