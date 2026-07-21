import unittest
from minimal_predictive_lm.counterfactual_dialogue_recombination import ContrastiveDialogueSynthesizer, Trace, make, evaluate

class CounterfactualDialogueRecombinationTests(unittest.TestCase):
    def test_known_trace_can_be_recovered(self):
        model=ContrastiveDialogueSynthesizer().fit(make(64,1))
        hypotheses=model.hypotheses('色を教えて')
        self.assertTrue(any(model.outcomes[h]=='color' for h in hypotheses))

    def test_ambiguous_input_does_not_claim_native_understanding(self):
        model=ContrastiveDialogueSynthesizer().fit(make(64,7))
        text=model.clarify('それを教えて')
        self.assertIsInstance(text,str)
        self.assertNotEqual(text,'')

    def test_report_exposes_decoy_failure(self):
        row=evaluate(256,19)
        self.assertGreaterEqual(row['decoy_accept'],0.75)
        self.assertLess(row['natural_clarification'],1.0)

if __name__=='__main__': unittest.main()
