# Sessie Handover: Islamic Reminders

**Afsluitdatum:** 2026-06-28 17:11 (Europe/Amsterdam)
**Project:** islamic-reminders
**Repo:** https://github.com/niliacuss/islamic-reminders (PUBLIC)
**Branch:** `main`
**Werkkopie deze sessie:** `D:\Claude\Islam Reminders\islamic-reminders`
(let op: er bestaat ook een tweede clone op `C:\Users\fessa\Documents\Claude\Islam Reminders\islamic-reminders`, beide volgen dezelfde remote, sync vóór elke sessie)
**Laatste inhoudelijke commit:** `ced2f93` (opening-polish), plus de handover-commit van deze /close.

## Eindstatus

- ✅ **VOL JAAR COMPLEET: 1095 reminders in `reminders.json` = 365 dagen unieke rotatie.**
- ✅ Productie draait vlekkeloos via cron-job.org (3 reminders/dag, `repository_dispatch` naar GitHub Actions naar Telegram).
- ✅ Dedup over de hele collectie: 0 paren boven 0.40 Jaccard, 0 zelfde-dag rotatie-clusters.
- ✅ Geen pending changes na deze handover-commit.

## Wat is in deze sessie gedaan (chronologisch)

1. Hervat via `/resume`; ontdekt dat de cwd (`D:`) een tweede, achterlopende clone was, gesynct met `main` (43 commits achter).
2. Failure-mail onderzocht: de 20:00-reminder van 27 juni faalde door een tijdelijke Telegram-timeout; de backup schedule-cron leverde hem 37 minuten later alsnog. Geen actie nodig, redundantie werkte.
3. Content uitgebreid van 630 naar 1095 (vol jaar):
   - Batch 8 (dagen 211-240, 720 totaal): commit `63cd488`
   - Batch 9 (241-270, 810): `fa08134`
   - Batch 10 (271-300, 900): `1348d2e`
   - Batch 11 (301-330, 990): `e9994a0`, geschreven met 5 parallelle Opus-subagents
   - Batch 12 + slot (331-365, 1095, vol jaar): `14019d9`, 6 parallelle subagents
   - Elke batch: schrijven, Jaccard-scan (drempel 0.40), additieve merge, commit, `git pull --rebase`, push.
4. Kwaliteit-finetune:
   - Volledige Jaccard-matrix over alle 1095 (`analyze.py`): 1 echt paar boven 0.40 plus 1 getripliceerde du'a gevonden en gefixt. Commit `dbfdba1`.
   - Opening-variatie polish: 12 entries' openingen gevarieerd tegen zelfde-dag herhaling. Commit `ced2f93`.
5. `/close` command aangepast: handover nu naar 4 locaties inclusief Obsidian plus gedateerde naam, geldt voor alle code-sessies. Gedocumenteerd in basic-memory `tools/automation/`.

## Open vragen / wachtende werkzaamheden

- Vol jaar is bereikt; **geen nieuwe content meer aanbevolen** (themapool uitgeput, zou geforceerd aanvoelen).
- Optioneel: theologische steekproef van de verhalende subagent-entries uit batch 11-12 (al gecontroleerd tijdens samenvoegen).
- PAT voor cron-job.org vervalt rond mei 2027: vernieuwen plus headers updaten.

## Bekende valkuilen geleerd

- Twee clones (`C:` en `D:`) van dezelfde repo; sync vóór elke sessie, anders werk je in de verkeerde of loop je achter.
- Subagents: geef ALTIJD exacte thema-seeds. Open-ended "kies zelf N hadiths" liet de slot-agent beroemde, al-bestaande hadiths kiezen (100 delen barmhartigheid, wolken-hadith), die moesten vervangen worden.
- Productie schrijft `.last_sent.json` bot-commits naar `main`; doe `git pull --rebase` vlak voor elke push.
- Windows: python via Git Bash kan `/c/`-mountpaden niet openen, gebruik `C:/`-paden; reconfigureer stdout naar utf-8 voor de emoji's.

## Tooling (in scratchpad)

`analyze.py` (volledige Jaccard-matrix plus zelfde-dag clustercheck), `openings.py` (opening-verdeling), `scan.py` (nieuw-vs-bestaand, pas NEW-pad aan per batch), plus backups per tussenstand (630, 720, 810, 900, 990). Pad: `C:\Users\fessa\AppData\Local\Temp\claude\D--Claude-Islam-Reminders\<sessie-id>\scratchpad`.

## Snel hervatten (volgende sessie)

```
Lees D:\Claude\Islam Reminders\islamic-reminders\SESSIE_HANDOVER.md plus basic-memory
projects/islamic-reminders/ en de auto-memory islamic_reminders_uniqueness.md. Het
Islamic Reminders project staat op 1095 reminders (vol jaar). Geen nieuwe content nodig;
eventueel kwaliteits-finetune of een theologische steekproef van batch 11-12.
```

## Belangrijke commands

```bash
cd "D:\Claude\Islam Reminders\islamic-reminders"
git pull --ff-only origin main
python -c "import json;print(len(json.load(open('reminders.json',encoding='utf-8'))))"   # 1095
gh run list --workflow=send-reminder.yml --limit=5
```

## Verwante basic-memory notes

- `projects/islamic-reminders/` (alle sessie- en project-notes)
- `tools/automation/islamic-reminders-automation-setup` (cron-job.org + Actions + Telegram setup)
- `tools/automation/close-command-handover-naar-4-locaties-met-obsidian-en-gedateerde-naam` (de /close wijziging van deze sessie)
