#!/usr/bin/env python3
"""Maak reminders_gedateerd.json uit markdown-bestanden met reminders.

Elk bericht staat in een codeblok (```) direct onder een kop zoals:

    ### 1. Dag 1, 10:00          (gewone nummers: reeks vanaf 1 december)
    ### N1. Dag 1, 10:00         (N-nummers: reeks vanaf 25 november)
    ### 37. 8 december, 10:00    (datum in de kop mag ook)
    ### 2026-12-08 10:00         (alleen datum en tijd, zonder nummer, mag ook)

Tekst buiten het codeblok (zoals de regel "Bron:") wordt niet meegenomen.

Datum en slot volgen uit het nummer: nummer k in een reeks met startdatum S
geeft dag S + (k-1) // 5 en slot (k-1) % 5 (slot 0-4 = 10, 13, 16, 19, 22 uur).
Staan er ook "Dag X", een datum of een tijd in de kop, dan moeten die kloppen
met het nummer; anders stopt het script met een foutmelding. "Dag 1" is de
eerste dag van de reeks (bij N: 25 november, zonder letter: 1 december).

Gebruik (geef altijd ALLE bronbestanden tegelijk mee; het uitvoerbestand wordt
volledig overschreven):

    python scripts/maak_gedateerd.py nov.md proefweek.md dec8-19.md dec20-31.md --vereis-volledig

Opties:
    --uit PAD                 uitvoerbestand (standaard: reminders_gedateerd.json in de repo)
    --van / --tot DATUM       toegestane periode (standaard 2026-11-25 t/m 2026-12-31)
    --vereis-volledig         fout als er in die periode een dag ontbreekt
    --sta-placeholders-toe    alleen voor tests: "[... invullen]" niet als fout zien
    --alleen-controleren      niets schrijven, alleen controleren
    --toon                    per reminder tonen op welke datum en welk slot hij komt
    --reeks LETTER=DATUM      startdatum van een reeks aanpassen of toevoegen
                              (zonder letter: --reeks "=2026-12-01")

Exitcode 0 = gelukt, 1 = fouten gevonden (er is dan niets geschreven).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_DIR / "reminders_gedateerd.json"
SLOTS_PER_DAY = 5
SLOT_TIMES = ("10:00", "13:00", "16:00", "19:00", "22:00")
TIME_TO_SLOT = {(10, 0): 0, (13, 0): 1, (16, 0): 2, (19, 0): 3, (22, 0): 4}
TELEGRAM_MAX_LEN = 4096
DEFAULT_SERIES = {"N": date(2026, 11, 25), "": date(2026, 12, 1)}

# Zelfde patroon als in send_reminder.py.
PLACEHOLDER_RE = re.compile(
    r"\[[^\]\n]*(?:invullen|todo|nakijken|placeholder)[^\]\n]*\]", re.IGNORECASE
)
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
NUMBERED_RE = re.compile(r"^([A-Za-z]?)(\d+)\s*[.):]\s*(.*)$")  # "12." of "N12."
FENCE_RE = re.compile(r"^\s*(```|~~~)")
DAG_RE = re.compile(r"\bdag\s+(\d+)\b", re.IGNORECASE)
TIME_RE = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")
ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
NL_DATE_RE = re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b")
MONTHS = {
    "januari": 1, "jan": 1, "februari": 2, "feb": 2, "maart": 3, "mrt": 3,
    "april": 4, "apr": 4, "mei": 5, "juni": 6, "jun": 6, "juli": 7, "jul": 7,
    "augustus": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9,
    "oktober": 10, "okt": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}
MONTH_DATE_RE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b\.?"
    r"(?:\s+(\d{4}))?",
    re.IGNORECASE,
)
THEMA_RE = re.compile(r"Thema:\s*(.+)")
DASHES = ("—", "–")  # em dash, en dash


def telegram_length(text: str) -> int:
    """Lengte zoals Telegram telt (UTF-16; de meeste emoji tellen als 2)."""
    return len(text.encode("utf-16-le")) // 2


def parse_date_in(text: str, default_year: int) -> tuple[date | None, str]:
    """Zoek een datum in een kop. Geeft (datum, kop zonder de datum)."""
    for regex, build in (
        (ISO_DATE_RE, lambda m: (int(m[1]), int(m[2]), int(m[3]))),
        (NL_DATE_RE, lambda m: (int(m[3]), int(m[2]), int(m[1]))),
        (
            MONTH_DATE_RE,
            lambda m: (int(m[3]) if m[3] else default_year, MONTHS[m[2].lower()], int(m[1])),
        ),
    ):
        m = regex.search(text)
        if m:
            y, mo, d = build(m)
            try:
                return date(y, mo, d), text[: m.start()] + " " + text[m.end():]
            except ValueError:
                raise ValueError(f"ongeldige datum '{m[0]}'")
    return None, text


class Heading:
    def __init__(self, source: str, line_no: int, raw: str):
        self.source = source
        self.line_no = line_no
        self.raw = raw
        self.prefix: str | None = None
        self.number: int | None = None
        self.block: list[str] | None = None

    @property
    def where(self) -> str:
        return f"{self.source}:{self.line_no} '{self.raw}'"

    @property
    def label(self) -> str:
        if self.number is None:
            return "-"
        return f"{self.prefix}{self.number}"


def read_source(path: Path, errors: list[str], warnings: list[str]) -> list[Heading]:
    """Lees een markdownbestand en geef de reminder-koppen met hun codeblok."""
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    found: list[Heading] = []
    pending: Heading | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith(marker):
                j += 1
            if j >= len(lines):
                errors.append(f"{path.name}:{i + 1} codeblok wordt niet afgesloten")
                break
            block = lines[i + 1 : j]
            if pending is None:
                warnings.append(
                    f"{path.name}:{i + 1} codeblok zonder reminder-kop overgeslagen"
                )
            elif pending.block is not None:
                errors.append(f"{pending.where}: meer dan een codeblok onder deze kop")
            else:
                pending.block = block
            i = j + 1
            continue

        heading = HEADING_RE.match(line)
        if heading:
            title = heading.group(1)
            numbered = NUMBERED_RE.match(title)
            has_date_and_time = (
                ISO_DATE_RE.search(title) or NL_DATE_RE.search(title)
                or MONTH_DATE_RE.search(title)
            ) and TIME_RE.search(title)
            if numbered or has_date_and_time:
                pending = Heading(path.name, i + 1, title)
                if numbered:
                    pending.prefix = numbered.group(1).upper()
                    pending.number = int(numbered.group(2))
                found.append(pending)
            else:
                pending = None  # andere kop: losse codeblokken eronder horen er niet bij
        i += 1
    return found


def resolve(h: Heading, series: dict[str, date], default_year: int) -> tuple[date, int]:
    """Bepaal (datum, slot) van een kop. Geeft ValueError bij tegenstrijdigheden."""
    rest = h.raw
    start = None
    from_number = None
    if h.number is not None:
        if h.prefix not in series:
            raise ValueError(
                f"onbekende reeks-letter '{h.prefix}' (bekend: "
                + ", ".join(repr(k) for k in series) + "); gebruik --reeks"
            )
        if h.number < 1:
            raise ValueError("nummer moet 1 of hoger zijn")
        start = series[h.prefix]
        k = h.number - 1
        from_number = (start + timedelta(days=k // SLOTS_PER_DAY), k % SLOTS_PER_DAY)
        rest = NUMBERED_RE.match(h.raw).group(3)

    year = start.year if start else default_year
    explicit_date, rest = parse_date_in(rest, year)

    slot_from_time = None
    t = TIME_RE.search(rest)
    if t:
        key = (int(t[1]), int(t[2]))
        if key not in TIME_TO_SLOT:
            raise ValueError(
                f"tijd {t[0]} is geen slot (toegestaan: {', '.join(SLOT_TIMES)})"
            )
        slot_from_time = TIME_TO_SLOT[key]

    day_from_dag = None
    d = DAG_RE.search(rest)
    if d:
        if start is None:
            raise ValueError("'Dag X' zonder nummer: onduidelijk vanaf welke datum")
        day_from_dag = start + timedelta(days=int(d[1]) - 1)

    days = {
        name: value
        for name, value in (
            ("nummer", from_number[0] if from_number else None),
            ("datum in de kop", explicit_date),
            ("Dag X", day_from_dag),
        )
        if value is not None
    }
    slots = {
        name: value
        for name, value in (
            ("nummer", from_number[1] if from_number else None),
            ("tijd", slot_from_time),
        )
        if value is not None
    }
    if len(set(days.values())) > 1:
        detail = ", ".join(f"{n} -> {v.isoformat()}" for n, v in days.items())
        raise ValueError(f"datum klopt niet: {detail}")
    if len(set(slots.values())) > 1:
        detail = ", ".join(f"{n} -> {SLOT_TIMES[v]}" for n, v in slots.items())
        raise ValueError(f"tijdslot klopt niet: {detail}")
    if not days or not slots:
        raise ValueError("datum of tijdslot niet te bepalen")
    return next(iter(days.values())), next(iter(slots.values()))


def clean_block(block: list[str]) -> str:
    lines = [line.rstrip() for line in block]
    return "\n".join(lines).strip("\n").strip()


def parse_series(values: list[str]) -> dict[str, date]:
    series = dict(DEFAULT_SERIES)
    for value in values:
        letter, sep, iso = value.partition("=")
        if not sep:
            raise argparse.ArgumentTypeError(f"--reeks verwacht LETTER=DATUM, kreeg '{value}'")
        series[letter.strip().upper()] = date.fromisoformat(iso.strip())
    return series


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Maak reminders_gedateerd.json uit markdown met reminders."
    )
    parser.add_argument("bronnen", nargs="+", type=Path, help="markdown-bestanden")
    parser.add_argument("--uit", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--van", type=date.fromisoformat, default=date(2026, 11, 25))
    parser.add_argument("--tot", type=date.fromisoformat, default=date(2026, 12, 31))
    parser.add_argument("--vereis-volledig", action="store_true")
    parser.add_argument("--sta-placeholders-toe", action="store_true")
    parser.add_argument("--alleen-controleren", action="store_true")
    parser.add_argument("--toon", action="store_true")
    parser.add_argument("--reeks", action="append", default=[], metavar="LETTER=DATUM")
    args = parser.parse_args(argv)
    try:
        series = parse_series(args.reeks)
    except (argparse.ArgumentTypeError, ValueError) as e:
        parser.error(str(e))

    errors: list[str] = []
    warnings: list[str] = []
    headings: list[Heading] = []
    for path in args.bronnen:
        if not path.is_file():
            errors.append(f"bestand niet gevonden: {path}")
            continue
        headings.extend(read_source(path, errors, warnings))

    seen_labels: dict[str, Heading] = {}
    by_slot: dict[tuple[date, int], tuple[Heading, dict]] = {}
    placeholders = 0
    for h in headings:
        if h.number is not None:
            if h.label in seen_labels:
                errors.append(f"{h.where}: nummer {h.label} komt ook voor in {seen_labels[h.label].where}")
                continue
            seen_labels[h.label] = h
        if h.block is None:
            errors.append(f"{h.where}: geen codeblok onder deze kop")
            continue
        try:
            day, slot = resolve(h, series, args.van.year)
        except ValueError as e:
            errors.append(f"{h.where}: {e}")
            continue
        if not (args.van <= day <= args.tot):
            errors.append(
                f"{h.where}: valt op {day.isoformat()}, buiten {args.van.isoformat()}"
                f" t/m {args.tot.isoformat()}"
            )
            continue
        if (day, slot) in by_slot:
            other = by_slot[(day, slot)][0]
            errors.append(f"{h.where}: {day} {SLOT_TIMES[slot]} is al bezet door {other.where}")
            continue

        text = clean_block(h.block)
        if not text:
            errors.append(f"{h.where}: codeblok is leeg")
            continue
        length = telegram_length(text)
        if length > TELEGRAM_MAX_LEN:
            errors.append(f"{h.where}: {length} tekens, Telegram staat max {TELEGRAM_MAX_LEN} toe")
        for m in PLACEHOLDER_RE.finditer(text):
            placeholders += 1
            msg = f"{h.where}: placeholder {m[0]}"
            (warnings if args.sta_placeholders_toe else errors).append(msg)
        if any(dash in text for dash in DASHES):
            warnings.append(f"{h.where}: bevat een em dash of en dash")
        thema_match = THEMA_RE.search(text)
        thema = thema_match.group(1).strip() if thema_match else ""
        if not thema:
            warnings.append(f"{h.where}: geen regel 'Thema:' gevonden")
        by_slot[(day, slot)] = (h, {"text": text, "thema": thema})

    days: dict[date, dict[int, tuple[Heading, dict]]] = {}
    for (day, slot), item in by_slot.items():
        days.setdefault(day, {})[slot] = item
    for day, slots in sorted(days.items()):
        missing = [SLOT_TIMES[s] for s in range(SLOTS_PER_DAY) if s not in slots]
        if missing:
            errors.append(f"{day.isoformat()}: onvolledig, ontbreekt {', '.join(missing)}")

    total_days = (args.tot - args.van).days + 1
    missing_days = [
        (args.van + timedelta(days=n)).isoformat()
        for n in range(total_days)
        if args.van + timedelta(days=n) not in days
    ]
    if missing_days:
        msg = (
            f"{len(missing_days)} van {total_days} dagen ontbreken"
            f" (daar geldt de oude rotatie): {', '.join(missing_days)}"
        )
        (errors if args.vereis_volledig else warnings).append(msg)

    if args.toon:
        print("Reminder -> datum en slot:")
        for (day, slot), (h, entry) in sorted(by_slot.items()):
            print(f"  {h.label:>5}  {day.isoformat()} {SLOT_TIMES[slot]}  {entry['thema']}  ({h.source})")

    print(f"Bronnen: {len(args.bronnen)} | koppen: {len(headings)} | geplaatst: {len(by_slot)}"
          f" | dagen: {len(days)} van {total_days} | placeholders: {placeholders}")
    for day, slots in sorted(days.items()):
        lengths = [telegram_length(e["text"]) for _, e in slots.values()]
        labels = ", ".join(slots[s][0].label for s in sorted(slots))
        print(f"  {day.isoformat()}: {len(slots)} slots ({labels}), {min(lengths)}-{max(lengths)} tekens")
    for w in warnings:
        print(f"WAARSCHUWING: {w}")
    for e in errors:
        print(f"FOUT: {e}")

    if errors:
        print(f"{len(errors)} fout(en): niets geschreven.")
        return 1
    if args.alleen_controleren:
        print("Controle geslaagd (--alleen-controleren: niets geschreven).")
        return 0

    out = {
        day.isoformat(): [slots[s][1] for s in range(SLOTS_PER_DAY)]
        for day, slots in sorted(days.items())
    }
    tmp = args.uit.with_name(args.uit.name + ".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, args.uit)
    print(f"Geschreven: {args.uit} ({len(out)} dagen, {len(by_slot)} berichten).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
