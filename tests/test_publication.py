import unittest,json
from pathlib import Path
import srt,nbformat,hashlib
from course.lesson import SEGMENTS
ROOT=Path(__file__).resolve().parents[1]
class PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.e=json.loads((ROOT/'course/publication_events.json').read_text(encoding='utf-8'))
    def test_measured_contiguous_complete_clock(self):
        e=self.e;self.assertEqual(e['status'],'MEASURED');self.assertEqual(e['duration_frames'],21600)
        self.assertEqual(e['scenes'][0]['start_frame'],0);self.assertEqual(e['scenes'][-1]['end_frame'],21600)
        self.assertTrue(all(a['end_frame']==b['start_frame'] for a,b in zip(e['scenes'],e['scenes'][1:])))
        self.assertEqual([s['text'] for s in e['scenes']],[s['text'] for s in SEGMENTS])
    def test_prediction_and_review_bounds(self):
        for q in self.e['quizzes']:
            scene=self.e['scenes'][q['scene']]
            self.assertLess(scene['speech_end_frame'],q['frame']);self.assertLess(q['frame'],q['reveal_frame']-4*30)
            self.assertGreaterEqual((q['reveal_frame']-q['hold_start_frame'])/30,6)
            self.assertLessEqual((q['reveal_frame']-q['hold_start_frame'])/30,10)
            self.assertLess(q['review_seconds'],q['time_seconds'])
    def test_actual_caption_text_and_bounds(self):
        actual=list(srt.parse((ROOT/'narration/lecture.srt').read_text(encoding='utf-8')))
        self.assertEqual(' '.join(c.content for c in actual).split(),' '.join(s['text'] for s in SEGMENTS).split())
        self.assertTrue(all(0<=c.start.total_seconds()<c.end.total_seconds()<=720 for c in actual))
        self.assertTrue(all(a.end<=b.start for a,b in zip(actual,actual[1:])))
    def test_spoken_highlights_and_chunks(self):
        for s in self.e['scenes']:
            if s['highlight_frame'] is not None:self.assertTrue(s['start_frame']<=s['highlight_frame']<s['speech_end_frame'])
        for c in self.e['narration']:self.assertTrue(0<=c['start_frame']<c['end_frame']<=21600)
    def test_notebook_embeds_canonical_model(self):
        book=nbformat.read(ROOT/'lab/Quantum_Formalism_Lab.ipynb',4)
        model=(ROOT/'course/physics.py').read_text(encoding='utf-8')
        self.assertEqual(book.metadata.canonical_model_sha256,hashlib.sha256(model.encode()).hexdigest())
        self.assertTrue(any(c.cell_type=='code' and c.source==model for c in book.cells))
if __name__=='__main__':unittest.main()
