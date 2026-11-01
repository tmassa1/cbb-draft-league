"""Fetch ESPN Division I directory and propose team IDs for commissioner review.
Does not overwrite data/draft.csv. Writes data/espn_id_review.csv.
Run: python scripts/match_espn_ids.py
"""
import csv, difflib, re, sys
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
URL='https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams'
ALIASES={
    'UConn':['Connecticut','UConn Huskies'],
    'St. John\'s':['St. John\'s (NY)','St Johns'],
    'Saint Louis':['Saint Louis Billikens','St. Louis'],
    'Miami (FL)':['Miami Hurricanes','Miami (FL) Hurricanes'],
    'Miami (OH)':['Miami (OH) RedHawks','Miami RedHawks'],
    'McNeese':['McNeese State','McNeese Cowboys'],
    'North Carolina':['North Carolina Tar Heels','UNC'],
    'Saint Mary\'s':['Saint Mary\'s Gaels','Saint Mary\'s (CA)'],
    'NC State':['North Carolina State','NC State Wolfpack'],
    'UC San Diego':['UCSD','UC San Diego Tritons'],
    'East Tennessee State':['ETSU','East Tennessee State Buccaneers'],
    'Charleston':['College of Charleston','Charleston Cougars'],
    'South Florida':['South Florida Bulls','USF Bulls'],
    'Western Kentucky':['WKU','Western Kentucky Hilltoppers'],
    'UNC Wilmington':['UNCW','UNC Wilmington Seahawks'],
    'Penn':['Pennsylvania Quakers','Penn Quakers'],
}
def norm(s): return re.sub('[^a-z0-9]','',s.lower())
def main():
    with (ROOT/'data/draft.csv').open(newline='',encoding='utf-8') as f: draft=list(csv.DictReader(f))
    try:
        resp=requests.get(URL,params={'limit':500,'groups':50},timeout=30)
        resp.raise_for_status()
        payload=resp.json()
        teams=payload.get('sports',[{}])[0].get('leagues',[{}])[0].get('teams',[])
        teams=[entry.get('team',{}) for entry in teams]
        if len(teams)<200: raise RuntimeError(f'Only {len(teams)} teams returned, directory appears incomplete; no IDs accepted')
    except Exception as exc:
        sys.exit(f'ESPN lookup failed: {exc}. Try again later; no draft files changed.')
    results=[]
    for r in draft:
        name=r['team']; variants=[name]+ALIASES.get(name,[])
        scored=[]
        for t in teams:
            names=[t.get(k,'') for k in ('displayName','name','shortDisplayName','abbreviation','location')]
            if any(norm(v)==norm(n) for v in variants for n in names if n): score=1.0
            else: score=max((difflib.SequenceMatcher(None,norm(v),norm(n)).ratio() for v in variants for n in names if n),default=0)
            scored.append((score,t))
        scored.sort(key=lambda a:a[0],reverse=True)
        best=scored[0];runner=scored[1];confident=best[0]>=0.95 and best[0]-runner[0]>=0.08
        results.append({'pick':r['pick'],'manager':r['manager'],'draft_team':name,'conference':r['conference'],
        'suggested_espn_id':best[1].get('id',''),'espn_name':best[1].get('displayName',''),
        'confidence':round(best[0],3),'runner_up':runner[1].get('displayName',''),'review_status':'REVIEW' if not confident else 'CANDIDATE — VERIFY'})
    out=ROOT/'data/espn_id_review.csv'
    with out.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    print(f'Wrote {out}; {len(teams)} directory teams, {len(results)} draft selections, {sum(r["review_status"]=="REVIEW" for r in results)} ambiguous suggestions')
    print('Review every row before populating ESPN IDs in data/draft.csv; no automatic changes made.')
if __name__=='__main__': main()
