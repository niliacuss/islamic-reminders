# Sessie Handover — Islamic Reminders

**Afsluitdatum:** 2026-06-09 01:09 (Europe/Amsterdam)
**Project:** islamic-reminders
**Repo:** https://github.com/niliacuss/islamic-reminders (PUBLIC)
**Branch:** `main`
**Worktree-pad:** `C:\Users\fessa\Documents\Claude\Islam Reminders\islamic-reminders`
**Laatste commit:** `8d41b82` — "Add 90 reminders for days 181-210 (total 630)"

## Eindstatus

- ✅ Productie draait vlekkeloos via cron-job.org (sinds 9 mei 2026, 17+ dagen op rij 3 reminders/dag binnen ~40s)
- ✅ 630 reminders in `reminders.json` = 210 dagen unieke rotatie
- ✅ Vanaf vandaag uniek t/m ~21 december 2026
- ✅ Geen pending changes, alles gepusht naar `main`
- ✅ Repo is public sinds 8 mei 2026 (onbeperkte gratis Actions)

## Wat is deze sessie gedaan (chronologisch)

### Fase 1 — Basis (22 april 2026, sessie-start)

- Repo `niliacuss/islamic-reminders` gekloond
- `send_reminder.py`, workflow YAML, `requirements.txt`, `.gitignore` opgezet
- 90 originele reminders door user aangeleverd, in `reminders.json` geplaatst
- Live test bevestigde Telegram delivery werkte (chat ID `5648739789`)
- Slot-windows (10-14/15-19/20-23) + `.last_sent.json` state-file ingevoerd
- Multi-recipient support (`TELEGRAM_CHAT_ID_2`) toegevoegd

### Fase 2 — Content uitbreiding (22 april - 26 mei 2026)

- Batch 2: dag 31-60 (90 reminders)
- Batch 3: dag 61-90
- Batch 4: dag 91-120
- Batch 5: dag 121-150
- Batch 6: dag 151-180
- Batch 7: dag 181-210

### Fase 3 — Scheduling problemen oplossen (7-8 mei 2026)

- GitHub Actions cron bleek onbetrouwbaar (1-2 reminders gemist per dag)
- Frequentie eerst verhoogd naar 4×/uur off-peak (`7,22,37,52 8-22 * * *`)
- Hielp niet voldoende → repo public gemaakt, fine-grained PAT aangemaakt
- Cron-job.org opgezet (3 jobs, 10/15/20 Europe/Amsterdam)
- Workflow uitgebreid met `repository_dispatch` event-type `send-reminder`

### Fase 4 — Dedup en stijl (25-26 mei 2026, 9 juni)

- User signaleerde dat hij reminders dubbel had gezien
- Jaccard token-overlap scan uitgevoerd op alle 540 entries
- 5 echte duplicaten gevonden + gefixt (Musa-put, Rust-graf, Kronen, Masjid-verlaten, Du'a-dankbaarheid)
- Batch 7 (90 nieuw) toegevoegd met scan vooraf
- Eindstand: 0 paren boven Jaccard 0.40 in hele DB
- Basic-memory notes geschreven (overview, scheduler-evolution, automation-setup, content-database, chat-archief)
- `UserPromptSubmit` hook in `settings.json` aangemerkt → rapportagestijl met `##` headers + `## Vervolgacties` blok

## Open vragen / wachtende werkzaamheden

- **Batch 8-12 nog te schrijven** — nog ~465 reminders nodig voor vol jaar (1095 = 365 × 3)
- **Themapool wordt smaller** — alle 99 Namen + de meeste hopeful Quranische beschrijvingen zijn gebruikt; volgende batches leunen op verhalen + concepten + du'a
- **PAT vervalt over ~11 maanden** (aangemaakt 8 mei 2026, 1-jaars termijn) → vernieuwen voor afloop + cron-job.org headers updaten

## Bekende valkuilen geleerd

- **GitHub Actions cron is best-effort** — minuut 0 is drukst; `7,22,37,52` off-peak hielp pas redelijk
- **Native cron blijft onbetrouwbaar** ook met redundantie → externe scheduler nodig
- **Cron-job.org PAT-permission:** `Contents: Read and write`, NIET Read-only (Read-only geeft 403 op `/dispatches`)
- **Repo private = 2000 min/maand limiet** → bij hoge frequentie cron kun je in betaling lopen; public lost dit op
- **GitHub Actions rondt billable minuten af naar boven** per run, dus 30 sec = 1 minuut
- **Title/Name-checks vangen geen content-duplicaten** — zelfde hadith met andere titel/woorden glipt door; alleen Jaccard token-overlap scan vangt het
- **GitHub Actions workflow_run-events kunnen niet schedule events activeren** indien `last commit was a bot commit` — vandaar `[skip ci]` in state-commit
- **Workflow-edits hebben ~5-15 min propagatie** voor nieuwe schedule actief wordt
- **Concurrency-groep voorkomt parallel runs** maar serieert ze; bij hoge frequentie kan een queue ontstaan

## Snel hervatten (volgende sessie)

Plak in een nieuwe Claude Code sessie:

```
Lees C:\Users\fessa\Documents\Claude\Islam Reminders\islamic-reminders\SESSIE_HANDOVER.md
plus basic-memory notes onder projects/islamic-reminders/ en tools/automation/islamic-reminders-automation-setup.
Dat is de volledige context voor het Islamic Reminders project.
```

Of voor één specifieke taak (bv. batch 8):

```
We zijn op 630 reminders, 210 dagen rotatie. Schrijf batch 8 (dagen 211-240, 90 nieuwe reminders).
Lees eerst de bestaande reminders.json via Jaccard token-overlap scan om duplicaten te voorkomen.
Discipline staat in basic-memory note "islamic-reminders uniqueness discipline".
```

## Belangrijke commands voor de volgende sessie

```bash
# Werkdirectory
cd "C:\Users\fessa\Documents\Claude\Islam Reminders\islamic-reminders"

# Status checken
git log --oneline -5
gh run list --workflow=send-reminder.yml --limit=5

# Recente sends bekijken
git log --author="github-actions" --pretty=format:"%h %ad" --date=iso-local --since="2 days ago"

# State-file
cat .last_sent.json

# Reminder count
python -c "import json; print(len(json.load(open('reminders.json',encoding='utf-8'))))"
```

## Verwante basic-memory notes

- `projects/islamic-reminders/Islamic Reminders - Project Overview`
- `projects/islamic-reminders/Islamic Reminders - Scheduler Evolution`
- `projects/islamic-reminders/Islamic Reminders - Content Database`
- `tools/automation/Islamic Reminders - Automation Setup`
- `chat-archief/2026-05-26 - islamic-reminders cron-job.org migratie en batch 7`

## Auto-memory pointers

- `~/.claude/projects/C--Users-fessa-Documents-Claude-Islam-Reminders/memory/MEMORY.md`
- `~/.claude/projects/C--Users-fessa-Documents-Claude-Islam-Reminders/memory/islamic_reminders_uniqueness.md`
