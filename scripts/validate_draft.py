"""Validate draft selections before enabling ESPN syncing."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def validate(rows, require_ids=False):
    errors = []
    if len(rows) != 108:
        errors.append(f"Expected 108 picks; found {len(rows)}")
    managers = Counter(row.get('manager','').strip() for row in rows)
    if len(managers) != 18 or any(n != 6 for n in managers.values()):
        errors.append('Expected exactly 18 managers with 6 picks each')
    picks = [str(row.get('pick','')).strip() for row in rows]
    if set(picks) != set(map(str, range(1, 109))):
        errors.append('Picks must be unique whole numbers 1 through 108')
    teams = [row.get('team','').strip().casefold() for row in rows]
    if not all(teams) or len(set(teams)) != len(teams):
        errors.append('Missing or repeated team names')
    ids = [row.get('espn_id','').strip() for row in rows]
    present = [x for x in ids if x]
    if require_ids and len(present) != 108:
        errors.append(f'Expected 108 ESPN IDs; found {len(present)}')
    if len(present) != len(set(present)):
        errors.append('Repeated ESPN team IDs')
    return errors

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-ids', action='store_true')
    args = parser.parse_args()
    with (ROOT / 'data/draft.csv').open(newline='', encoding='utf-8') as file:
        records = list(csv.DictReader(file))
    findings = validate(records, require_ids=args.require_ids)
    if findings:
        raise SystemExit('Draft validation failed:\n- ' + '\n- '.join(findings))
    print(f'Draft valid: {len(records)} picks, 18 managers, 6 each; ESPN IDs present: {sum(bool(x.get("espn_id", "").strip()) for x in records)}')
