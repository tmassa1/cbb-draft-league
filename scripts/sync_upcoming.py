"""Fetch upcoming ESPN men's D-I games involving drafted teams.

Run: python scripts/sync_upcoming.py --days 7
Outputs data/upcoming_games.csv; no impact on league points.
"""
import argparse
import csv
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import requests

try:
    from .sync_espn import BASE, fetch_day, read_csv
except ImportError:
    from sync_espn import BASE, fetch_day, read_csv

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['game_id', 'start_utc', 'away_team', 'home_team', 'away_manager',
          'home_manager', 'away_drafted', 'home_drafted', 'spread',
          'away_ml', 'home_ml', 'status', 'away_score', 'home_score']


def moneyline(value):
    if value is None or value == '':
        return 'N/A'
    try:
        val = int(float(value))
        return f'+{val}' if val > 0 else str(val)
    except (TypeError, ValueError):
        return 'N/A'


def parse_event(event, draft_by_id):
    competitions = event.get('competitions') or []
    if not competitions:
        return None
    competition = competitions[0]
    competitors = competition.get('competitors') or []
    if len(competitors) != 2:
        return None
    by_side = {team.get('homeAway'): team for team in competitors}
    if 'home' not in by_side or 'away' not in by_side:
        return None
    home, away = by_side['home'], by_side['away']
    home_id = str(home.get('team', {}).get('id', ''))
    away_id = str(away.get('team', {}).get('id', ''))
    if not (home_id in draft_by_id or away_id in draft_by_id):
        return None
    status = competition.get('status', event.get('status', {})).get('type', {})
    start = event.get('date') or competition.get('date')
    if not start:
        return None
    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    start_dt = start_dt.astimezone(timezone.utc)
    eastern = ZoneInfo('America/New_York')
    if start_dt.astimezone(eastern).date() < datetime.now(eastern).date():
        return None
    state = status.get('state', 'pre')
    label = 'Final' if status.get('completed') or state == 'post' else ('Live' if state == 'in' else 'Upcoming')
    odds = (competition.get('odds') or [])
    market = odds[0] if odds else {}
    away_odds = market.get('awayTeamOdds') or {}
    home_odds = market.get('homeTeamOdds') or {}
    spread = market.get('details') or market.get('displayDetails') or 'N/A'
    return {
        'game_id': str(event.get('id', '')),
        'start_utc': start_dt.isoformat(),
        'away_team': away.get('team', {}).get('displayName', 'Unknown'),
        'home_team': home.get('team', {}).get('displayName', 'Unknown'),
        'away_manager': draft_by_id.get(away_id, {}).get('manager', ''),
        'home_manager': draft_by_id.get(home_id, {}).get('manager', ''),
        'away_drafted': 'Y' if away_id in draft_by_id else 'N',
        'home_drafted': 'Y' if home_id in draft_by_id else 'N',
        'spread': str(spread),
        'away_ml': moneyline(away_odds.get('moneyLine')),
        'home_ml': moneyline(home_odds.get('moneyLine')),
        'status': label,
        'away_score': str(away.get('score', '')),
        'home_score': str(home.get('score', '')),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--days', type=int, default=7)
    args = p.parse_args()
    if not 1 <= args.days <= 14:
        p.error('--days must be between 1 and 14')
    draft = read_csv(ROOT / 'data/draft.csv')
    ids = {row['espn_id'].strip(): row for row in draft if row.get('espn_id', '').strip()}
    if len(ids) != len(draft):
        raise RuntimeError('Draft has missing or duplicate ESPN IDs')
    today = datetime.now(ZoneInfo('America/New_York')).date()
    by_game = {}
    with requests.Session() as session:
        session.headers['User-Agent'] = 'CBBFantasyLeague/0.2 (private hobby scoreboard)'
        for offset in range(args.days + 1):
            day = today + timedelta(days=offset)
            for event in fetch_day(day, session):
                row = parse_event(event, ids)
                if row:
                    by_game[row['game_id']] = row
    rows = sorted(by_game.values(), key=lambda r: (r['start_utc'], r['game_id']))
    target = ROOT / 'data/upcoming_games.csv'
    with target.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved {len(rows)} upcoming games involving drafted teams')


if __name__ == '__main__':
    main()
