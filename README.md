# CBB Draft League — 2026–27 (13 managers)

78 real draft selections from 13 managers, six teams each. Four Streamlit tabs: League Standings, Manager Profiles, Daily Scoreboard, League Analytics.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

**Default is Demo.** These are fabricated game results, not official results. Real drafted teams appear in both modes. Live starts with zero games.

## ESPN IDs — verification required

```bash
python scripts/match_espn_ids.py
```

This connects to ESPN's unofficial team directory and produces `data/espn_id_review.csv` with candidate IDs and ambiguous matches. It does not change the live draft. Check each school against ESPN, especially Miami (FL), Miami (OH), Saint Mary's, South Florida, Charleston, and similarly named teams. Only then copy reviewed IDs into `data/draft.csv`'s `espn_id` column and verify:

```bash
python scripts/validate_draft.py --require-ids
```

## Score rules

`config/scoring.json`: regular/conference W +2 / L -1; NCAA tournament W +3 / L 0; Final Four W +5 total / L 0.

## Live automation safety

`.github/workflows/daily-update.yml` runs **manually only** until IDs are verified. `scripts/sync_espn.py` fetches completed ESPN games across D1 groups, but March/April game phases must be classified with verified `data/game_phases.csv` mappings. Check results before switching on a schedule. The importer deliberately excludes unidentified March/April games.

## Publish to existing GitHub repository

Upload project files to the existing repository, replacing `app.py`, `data/draft.csv`, `data/games_demo.csv`, `scripts/validate_draft.py`, and the workflow; add `scripts/match_espn_ids.py`, the verified draft source and updated tests. Maintain folder paths. Streamlit redeploys from main. Do not use the old `generate_demo.py` to recreate placeholder draft data.
