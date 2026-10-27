"""ESPN unofficial feed -> immutable completed-game rows, idempotent sync.

Usage:
  python scripts/sync_espn.py --start 2026-11-01 --end 2026-11-15
Run repeatedly; the entire specified date interval is refetched and refreshed.

Important: NCAA postseason phase is deliberately NOT inferred from ESPN `season.type`.
Conference tournament and NCAA rounds need explicit verified classification in
`data/game_phases.csv` before those games are added to season totals.
"""
import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import time
import requests
try:
    from .validate_draft import validate
except ImportError:  # Direct script execution
    from validate_draft import validate

BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['game_id','date','team','opponent','result','phase','source']

def read_csv(path):
    with open(path, newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    with open(path, 'w', newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def fetch_day(day, session):
    response = session.get(BASE,params={'dates':day.strftime('%Y%m%d'),'groups':50,'limit':500},timeout=25)
    response.raise_for_status()
    data=response.json()
    events=data.get('events', [])
    if len(events)>=500:
        raise RuntimeError(f'{day} reached the fetch limit; possible missing games')
    return events

def to_rows(events, lookup, phase_map):
    rows=[]
    for event in events:
        competitions=event.get('competitions', [])
        if not competitions: continue
        c=competitions[0]
        if not c.get('status', {}).get('type', {}).get('completed',False): continue
        contestants=c.get('competitors', [])
        if len(contestants)!=2: continue
        ids=[str(x.get('team',{}).get('id','')) for x in contestants]
        if not all(ids): continue
        game_id=str(event['id'])
        phase=phase_map.get(game_id)
        if not phase:
            # ESPN considers many conference tournament games regular-season.
            # Never silently mis-score unidentified games after this cutoff.
            game_day=date.fromisoformat(event['date'][:10])
            if game_day.month in (3,4):
                continue
            phase='regular'
        if phase=='exclude': continue
        winner_flags = [x.get('winner') for x in contestants]
        if winner_flags.count(True)!=1: continue
        for idx,espn_id in enumerate(ids):
            if espn_id not in lookup: continue
            rows.append({'game_id':game_id,'date':event['date'][:10], 'team':lookup[espn_id], 'opponent':contestants[1-idx]['team'].get('displayName','Opponent'), 'result':'W' if winner_flags[idx] else 'L','phase':phase,'source':'espn'})
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--start', required=True,help='YYYY-MM-DD')
    p.add_argument('--end', required=True,help='YYYY-MM-DD')
    args=p.parse_args()
    first,last=date.fromisoformat(args.start),date.fromisoformat(args.end)
    if first>last: raise ValueError('start after end')
    if (last-first).days > 90: raise ValueError('Sync at most 91 days at once')
    draft=read_csv(ROOT/'data/draft.csv')
    errors = validate(draft, require_ids=True)
    if errors: raise RuntimeError('Invalid draft: ' + '; '.join(errors))
    lookup={r['espn_id'].strip():r['team'] for r in draft}
    phases=read_csv(ROOT/'data/game_phases.csv')
    phase_map={r['game_id']:r['phase'] for r in phases}
    target=ROOT/'data/games_live.csv'
    old=read_csv(target)
    retained={ (r['game_id'],r['team']):r for r in old if not (first.isoformat()<=r['date']<=last.isoformat()) }
    new=[]
    with requests.Session() as s:
        s.headers['User-Agent']='CBBFantasyLeague/0.1 (private hobby scoreboard)'
        d=first
        while d<=last:
            new.extend(to_rows(fetch_day(d,s),lookup,phase_map))
            d+=timedelta(days=1)
            time.sleep(.15)
    for r in new:
        retained[(r['game_id'],r['team'])]=r
    write_csv(target, sorted(retained.values(),key=lambda r:(r['date'],r['game_id'],r['team'])))
    print(f'Synced {len(new)} game-team results in requested range, {len(retained)} total rows')

if __name__=='__main__': main()
