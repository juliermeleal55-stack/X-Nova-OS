import json
from pathlib import Path
import unittest
from integration.patch_review import summarize

BASE=json.loads((Path(__file__).resolve().parents[1]/'integration/tolerated_patch_review.json').read_text())


class PriorFailureReviewTests(unittest.TestCase):
    def test_all_nineteen_are_reviewed_but_not_claimed_validated(self):
        self.assertEqual(len(BASE['patches']),19)
        self.assertEqual(BASE['failed_modules'],1)
        self.assertEqual(sum(p['new_class_engine_fix'] for p in BASE['patches']),3)
        self.assertTrue(all(p['static_review']=='completed' and p['s24fe_validation']=='not-executed' for p in BASE['patches']))
        result=summarize([],{'donor_profile':{'model':'SM-S721B'}})
        self.assertEqual(result['counts'],{'passed':0,'failed':0,'not-executed':19})

    def test_executed_pass_failure_and_not_executed_are_distinct(self):
        events=[dict(kind='patch',patch=BASE['patches'][0]['patch'],status='passed'),dict(kind='patch',patch=BASE['patches'][1]['patch'],status='failed')]
        result=summarize(events,{})
        self.assertEqual(result['counts'],{'passed':1,'failed':1,'not-executed':17})

    def test_module_pass_or_later_retry_cannot_hide_failed_patch(self):
        name=BASE['patches'][0]['patch']
        result=summarize([dict(kind='module',patch=name,status='passed'),dict(kind='patch',patch=name,status='failed'),dict(kind='patch',patch=name,status='passed')],{})
        self.assertEqual(result['counts'],{'passed':0,'failed':1,'not-executed':18})
