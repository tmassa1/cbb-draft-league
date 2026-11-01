"""Deterministic demo data. NEVER use as real league results."""
from pathlib import Path
import random
import csv
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
TEAMS = '''Duke|North Carolina|Kansas|Kentucky|UConn|Houston|Gonzaga|Florida|Arizona|Tennessee|Purdue|Michigan State|Auburn|Alabama|Baylor|Iowa State|Texas Tech|Marquette|Wisconsin|Illinois|Michigan|Maryland|Ohio State|Indiana|UCLA|USC|Oregon|Washington|Nebraska|Iowa|Minnesota|Northwestern|Rutgers|Penn State|Virginia|Louisville|Clemson|NC State|Wake Forest|Georgia Tech|Miami|Florida State|Syracuse|Notre Dame|Pittsburgh|Boston College|Stanford|California|SMU|Virginia Tech|Texas|Texas A&M|Arkansas|Oklahoma|Oklahoma State|Missouri|Ole Miss|Mississippi State|LSU|Georgia|South Carolina|Vanderbilt|BYU|Utah|Colorado|Arizona State|Cincinnati|UCF|West Virginia|Kansas State|TCU|Saint Mary's|San Francisco|Santa Clara|Loyola Marymount|Pepperdine|Portland|San Diego|Pacific|VCU|Dayton|Saint Louis|Richmond|George Mason|Davidson|St. Bonaventure|Rhode Island|Duquesne|La Salle|Saint Joseph's|Fordham|George Washington|Loyola Chicago|Memphis|Tulane|North Texas|Wichita State|Temple|UAB|South Florida|Charlotte|FAU|Boise State|San Diego State|New Mexico|Colorado State|Utah State|Nevada'''.split('|')
assert len(TEAMS) == len(set(TEAMS)) == 108

def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def generate():
    DATA.mkdir(exist_ok=True)
    rng = random.Random(202627)
    shuffled = TEAMS[:]
    rng.shuffle(shuffled)
    managers = [f'Owner {i:02d}' for i in range(1, 19)]
    # Snake draft: all 108 teams appear exactly once.
    picks = []
    for round_idx in range(6):
        ordered = managers if round_idx % 2 == 0 else list(reversed(managers))
        for manager in ordered:
            pick = len(picks) + 1
            picks.append({'pick': pick, 'round': round_idx + 1, 'manager': manager, 'team': shuffled[pick - 1], 'espn_id': ''})
    write_csv(DATA / 'draft.csv', picks, ['pick', 'round', 'manager', 'team', 'espn_id'])
    # Fake results at 2026-12-15 only; explicitly labeled as mock in dashboard.
    start = date(2026, 11, 3)
    days = 43
    games = []
    for index, team in enumerate(shuffled):
        count = rng.randint(9, 14)
        match_days = sorted(rng.sample(range(days), count))
        for n, offset in enumerate(match_days):
            result = 'W' if rng.random() < (0.79 if index < 28 else 0.56 if index < 75 else 0.36) else 'L'
            games.append({'game_id': f'MOCK-{index:03d}-{n:02d}', 'date': (start+timedelta(days=offset)).isoformat(), 'team': team, 'opponent': 'Demo Opponent', 'result': result, 'phase': 'regular', 'source': 'demo'})
    write_csv(DATA / 'games_demo.csv', games, ['game_id', 'date', 'team', 'opponent', 'result', 'phase', 'source'])
    write_csv(DATA / 'games_live.csv', [], ['game_id', 'date', 'team', 'opponent', 'result', 'phase', 'source'])

if __name__ == '__main__':
    generate()
    print('Generated 18 managers, 108 unique teams, mock game history')
