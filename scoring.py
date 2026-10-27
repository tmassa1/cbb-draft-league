"""Pure scoring functions shared by the site, sync and tests."""
import pandas as pd
import json
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent / "config" / "scoring.json"


def load_rules(path=RULES_PATH):
    """Load commissioner rules at calculation time so changed rules rescore history."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"regular", "conference", "ncaa", "final_four"}
    if set(raw) != required or any(set(v) != {"win", "loss"} for v in raw.values()):
        raise ValueError("Scoring config must specify win/loss for every phase")
    if any(type(n) is not int for v in raw.values() for n in v.values()):
        raise ValueError("Scoring values must be integers")
    return {phase: (points["win"], points["loss"]) for phase, points in raw.items()}



def score_games(games: pd.DataFrame) -> pd.DataFrame:
    """One row per participating drafted team and completed game."""
    if games.empty:
        return games.assign(points=pd.Series(dtype=int))
    required = {"game_id", "team", "date", "result", "phase"}
    missing = required - set(games.columns)
    if missing:
        raise ValueError(f"Games missing columns: {', '.join(sorted(missing))}")
    rules = load_rules()
    g = games.copy()
    g = g[g.result.isin(["W", "L"])].copy()
    if not g.phase.isin(rules).all():
        raise ValueError(f"Unknown scoring phases: {g.loc[~g.phase.isin(rules), 'phase'].unique().tolist()}")
    if g.duplicated(["game_id", "team"]).any():
        raise ValueError("Duplicate game/team rows would double count points")
    g["points"] = [rules[phase][0 if result == "W" else 1] for phase, result in zip(g.phase, g.result)]
    g["date"] = pd.to_datetime(g["date"]).dt.normalize()
    return g


def scoring_summary(draft: pd.DataFrame, games: pd.DataFrame):
    sg = score_games(games)
    merged = sg.merge(draft[["manager", "team"]], on="team", how="inner", validate="many_to_one")
    team = draft[["manager", "team", "pick"]].merge(
        merged.groupby("team", as_index=False).agg(points=("points", "sum"), wins=("result", lambda x: (x == "W").sum()), losses=("result", lambda x: (x == "L").sum())),
        on="team", how="left", validate="one_to_one"
    ).fillna({"points": 0, "wins": 0, "losses": 0})
    for column in ("points", "wins", "losses"):
        team[column] = team[column].astype(int)
    managers = team.groupby("manager", as_index=False).agg(points=("points", "sum"), wins=("wins", "sum"), losses=("losses", "sum"), teams=("team", "count"))
    managers = managers.sort_values(["points", "wins", "manager"], ascending=[False, False, True]).reset_index(drop=True)
    managers.insert(0, "rank", managers.index + 1)
    return managers, team, merged
