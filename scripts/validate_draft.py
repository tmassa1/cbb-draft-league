"""Validate draft selections before enabling ESPN syncing."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def validate(rows, require_ids=False):
    errors = []
    if len(rows) != 78:
        errors.append(f"Expected 78 picks; found {len(rows)}")
    managers = Counter(row.get('manager','').strip() for row in rows)
    if len(managers) != 13 or any(n != 6 for n in managers.values()):
        errors.append('Expected exactly 13 managers with 6 picks each')
    picks = [str(row.get('pick','')).strip() for row in rows]
    if set(picks) != set(map(str, range(1, 79))):
        errors.append('Picks must be unique whole numbers 1 through 78')
    teams = [row.get('team','').strip().casefold() for row in rows]
    if not all(teams) or len(set(teams)) != len(teams):
        errors.append('Missing or repeated team names')
    ids = [row.get('espn_id','').strip() for row in rows]
    present = [x for x in ids if x]
    if require_ids and len(present) != 78:
        errors.append(f'Expected 78 ESPN IDs; found {len(present)}')
    if len(present) != len(set(present)):
        errors.append('Repeated ESPN team IDs')
    if rows and any(not row.get('conference', '').strip() for row in rows):
        errors.append('Missing school conference')
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
    print(f'Draft valid: {len(records)} picks, 13 managers, 6 each; ESPN IDs present: {sum(bool(x.get("espn_id", "").strip()) for x in records)}')
