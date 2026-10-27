import unittest
import pandas as pd
from scoring import score_games, scoring_summary

class TestScoring(unittest.TestCase):
    def test_rules(self):
        rows=[dict(game_id=str(i),team='Duke',date='2026-11-01',result=r,phase=p) for i,(p,r) in enumerate([('regular','W'),('regular','L'),('conference','W'),('ncaa','W'),('ncaa','L'),('final_four','W'),('final_four','L')])]
        self.assertEqual(score_games(pd.DataFrame(rows)).points.tolist(),[2,-1,2,3,0,5,0])
    def test_duplicate_detection(self):
        x=pd.DataFrame([dict(game_id='1',team='Duke',date='2026-11-01',result='W',phase='regular')]*2)
        with self.assertRaises(ValueError): score_games(x)
    def test_standings(self):
        draft=pd.DataFrame([{'manager':'Owner A','team':'Duke','pick':1},{'manager':'Owner B','team':'Kansas','pick':2}])
        games=pd.DataFrame([{'game_id':'1','team':'Duke','date':'2026-11-01','result':'W','phase':'regular'}])
        m,t,d=scoring_summary(draft,games)
        self.assertEqual(m.iloc[0]['manager'],'Owner A')
        self.assertEqual(m.iloc[0]['points'],2)
        self.assertEqual(len(t),2)

if __name__=='__main__': unittest.main()
