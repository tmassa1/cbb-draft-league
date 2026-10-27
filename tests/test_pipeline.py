import unittest
from pathlib import Path
import json
import tempfile
import pandas as pd
from scoring import score_games, load_rules
from scripts.validate_draft import validate
from scripts.sync_espn import to_rows

class PipelineTests(unittest.TestCase):
    def test_custom_rules_recalculate(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'rules.json'
            path.write_text(json.dumps({phase:{'win':4,'loss':-2} for phase in ('regular','conference','ncaa','final_four')}))
            self.assertEqual(load_rules(path)['ncaa'],(4,-2))
        self.assertEqual(score_games(pd.DataFrame([{'game_id':'game1','team':'Duke','date':'2026-11-20','result':'L','phase':'regular'}])).points.tolist(),[-1])

    def test_draft_rejects_duplicate_school(self):
        rows=[{'manager':f'Manager {i//6+1}','pick':str(i+1),'team':f'School {i}','espn_id':str(i+1)} for i in range(108)]
        self.assertEqual(validate(rows,require_ids=True),[])
        rows[1]['team']=rows[0]['team']
        self.assertTrue(any('team' in e.lower() for e in validate(rows,require_ids=True)))

    def test_espn_completed_game_and_non_drafted_opponent(self):
        def competitor(id,name,winner):
            return {'team':{'id':id,'displayName':name},'winner':winner}
        events=[{'id':'abc123','date':'2026-11-20T23:00Z','competitions':[{'status':{'type':{'completed':True}},'competitors':[competitor('150','Duke',True),competitor('9','Smaller School',False)]}]}]
        rows=to_rows(events,{'150':'Duke'}, {})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['result'],'W')
        self.assertEqual(rows[0]['opponent'],'Smaller School')
        self.assertEqual(rows[0]['phase'],'regular')
        self.assertEqual(score_games(pd.DataFrame(rows)).points.iloc[0],2)
        events[0]['competitions'][0]['status']['type']['completed']=False
        self.assertEqual(to_rows(events,{'150':'Duke'},{}),[])

    def test_postseason_requires_manual_phase(self):
        events=[{'id':'marchgame','date':'2027-03-21T22:00Z','competitions':[{'status':{'type':{'completed':True}},'competitors':[{'team':{'id':'1'},'winner':True},{'team':{'id':'2'},'winner':False}]}]}]
        self.assertEqual(to_rows(events,{'1':'Team A','2':'Team B'},{}),[])
        rows=to_rows(events,{'1':'Team A','2':'Team B'},{'marchgame':'ncaa'})
        self.assertEqual(len(rows),2)
        self.assertEqual(score_games(pd.DataFrame(rows)).points.tolist(),[3,0])

if __name__=='__main__': unittest.main()
