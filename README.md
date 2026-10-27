# CBB Draft League Dashboard (2026–27)

A mobile-friendly Streamlit site for 18 managers drafting 6 Division I teams each (108 distinct teams). Includes standings, manager pages, game logs, daily scoreboard, points trends, and draft analytics.

## Quick start (Windows)

1. Download/unzip this folder; install Python 3.11 or newer.
2. Open Command Prompt or PowerShell inside the `cbb-draft-dashboard` folder.
3. Run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

4. The site opens at `http://localhost:8501`. Choose **Demo** in the sidebar. All results are **fake** and generated from a fixed seed for test purposes.

## When the draft happens

Replace manager names and selected teams in `data/draft.csv`, retaining **one row per pick** and the columns `pick,round,manager,team,espn_id`. No team or ESPN ID can belong to multiple managers. ESPN IDs must match ESPN's own numeric Division I team identifier. Do not use an automatic fuzzy match without checking it; for example, multiple schools share mascots and abbreviations.

Select **Live** to view `data/games_live.csv`. Leave `games_demo.csv` untouched; it will never be merged into the live totals. To populate game results after you have filled all 108 IDs:

```powershell
python scripts/sync_espn.py --start 2026-11-01 --end 2026-11-15
```

Choose the correct dates. Re-running an interval updates or replaces prior results for those days, with no duplicate point awards. ESPN's public scoreboard is an **unofficial, undocumented feed** and may change or be unavailable. Refreshes will fail visibly rather than silently substitute fabricated game scores.

### Important postseason safeguard

Games in March/April are **not automatically scored** unless entered with explicit ESPN game IDs and scoring phase in `data/game_phases.csv`:

```csv
game_id,phase
401000001,conference
401000002,ncaa
401000003,final_four
```

These IDs are **examples**, not real games. You must classify each relevant conference tournament, NCAA first-four, early-round, semifinal and championship game. Phase names are `regular`, `conference`, `ncaa`, `final_four`, `exclude`. By default we assign **+5 total** for a Final Four win (not +3 plus a 5-point bonus); adjust `config/scoring.json` if your group decides otherwise. NCAA title-game winner is mapped to `final_four` only if your rules intend 5 points for that win as well. This needs agreement before live postseason scoring.

Other issues to confirm: exhibition games / non-D1 opponents / NIT and other postseason events. This MVP does **not** include those by default; consider explicit exclusions.

### Host for league mates

Push this folder to a GitHub repository, connect the repository at https://share.streamlit.io, select `app.py` as entrypoint and deploy. Share the resulting `*.streamlit.app` URL with everyone. GitHub Actions' `daily-update.yml` workflow can update `games_live.csv` each morning **after** all ESPN IDs have been added. It requires repository workflow write permissions, and may not execute on inactive repos or if scheduled jobs are disabled. Confirm update logs weekly. On free Streamlit Community Cloud, app may sleep after inactivity and wake when visited. Public URL access depends on your deployment visibility settings.

The automatic sync uses a rolling 6-day window for corrections. For historic backfills, run manual date-range calls of at most 91 days. A March/April classifications file must be maintained before that period.

## Project structure

- `app.py`: dashboard and navigation
- `scoring.py`: pure scoring, standings aggregation
- `data/draft.csv`: placeholder draft board / later real selections
- `data/games_demo.csv`: **fabricated sample results**
- `data/games_live.csv`: real imported results only
- `data/game_phases.csv`: reviewed postseason game-phase mapping
- `scripts/generate_demo.py`: deterministic synthetic league setup
- `scripts/sync_espn.py`: real ESPN scoreboard ingest
- `.github/workflows/daily-update.yml`: scheduled sync
- `tests/test_scoring.py`: basic scoring checks

## Scoring

Regular season + conference tournament = 2 points/W, -1/L. NCAA tournament = 3/W, 0/L. Final Four = 5/W, 0/L. Every game is counted once per drafted team by `(game_id, team)`.

## Version 1.1 — Pre-draft checks and editable scoring

This build centralizes the league scoring at `config/scoring.json`. **Edit only the numeric `win` and `loss` values** if the league votes to change points, then save the file and redeploy (push to GitHub once hosted). The dashboard reads this config and recalculates all historical game results with the new numbers. Game-phase classification still comes from `data/game_phases.csv` or the imported game log, so changing *which games count as Final Four* is a separate classification task.

Run checks from the project root:

```powershell
python -m unittest discover -s tests -v
python scripts/validate_draft.py
```

The draft validator will accept missing ESPN IDs for the pre-draft demo. After draft day, fill all IDs and use:

```powershell
python scripts/validate_draft.py --require-ids
```

**Do not** run `scripts/generate_demo.py` after entering real draft selections; it recreates the placeholder selections.

For GitHub upload, put the **contents of this project folder** in the repository root so `app.py`, `requirements.txt`, `config/`, `scripts/`, and `data/` are in the correct places. Include hidden `.github/` and `.streamlit/` folders. Choose `app.py` as Streamlit Community Cloud's main file. Deploy in Demo mode first. After launch, enable the Actions workflow only when the 108 actual team IDs have been verified and postseason handling is complete.

### Validation scope

Unit tests cover base scoring, duplicate protection, standings aggregation, draft constraints, completed vs incomplete ESPN fixture games, non-drafted opponents, and March postseason manual classification. These tests use local test fixtures; they are **not** a full end-to-end validation of real ESPN games or the hosting service. ESPN coverage and scheduling must be monitored during the season.
