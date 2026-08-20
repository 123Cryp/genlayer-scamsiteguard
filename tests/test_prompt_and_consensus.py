"""
Tests for `_build_prompt` (guardrail presence) and
`EQUIVALENCE_PRINCIPLE` (schema consistency with what submit_check
actually returns).
"""

import unittest

from tests._bootstrap import ScamSiteGuard, make_contract

_helper = make_contract()


class TestBuildPrompt(unittest.TestCase):
    def setUp(self):
        self.prompt = _helper._build_prompt(
            "scam-site.example", "Some evidence content about the site."
        )
        # Normalize whitespace/newlines for phrase-presence checks,
        # since the prompt's source text wraps some guardrail phrases
        # across lines for readability - the wrapping is cosmetic and
        # shouldn't make a substring check brittle.
        self.prompt_flat = " ".join(self.prompt.split())

    def test_contains_untrusted_data_framing(self):
        self.assertIn("UNTRUSTED DATA", self.prompt)

    def test_contains_injection_guardrail(self):
        self.assertIn("ignore previous instructions", self.prompt_flat.lower())
        self.assertIn("NOT a set of instructions", self.prompt_flat)

    def test_contains_target_domain_verbatim(self):
        self.assertIn("scam-site.example", self.prompt)

    def test_contains_evidence_content_verbatim(self):
        self.assertIn("Some evidence content about the site.", self.prompt)

    def test_contains_no_outside_knowledge_guardrail(self):
        self.assertIn("never on any outside or prior knowledge", self.prompt)

    def test_contains_skepticism_guardrail(self):
        self.assertIn("skepticism", self.prompt)

    def test_contains_neutral_mention_guardrail(self):
        self.assertIn("neutrally", self.prompt)

    def test_contains_insufficient_evidence_guardrail(self):
        self.assertIn("respond Unclear rather than", self.prompt_flat)

    def test_fixed_output_vocabulary_still_present(self):
        for word in ("IndicatesScam", "IndicatesLegitimate", "Unclear"):
            self.assertIn(word, self.prompt)
        self.assertIn("ONLY one single word", self.prompt)

    def test_markers_are_clearly_delimited(self):
        self.assertIn("<<<TARGET_DOMAIN>>>", self.prompt)
        self.assertIn("<<<END_TARGET_DOMAIN>>>", self.prompt)
        self.assertIn("<<<EVIDENCE_CONTENT>>>", self.prompt)
        self.assertIn("<<<END_EVIDENCE_CONTENT>>>", self.prompt)


class TestEquivalencePrinciple(unittest.TestCase):
    def setUp(self):
        self.principle = ScamSiteGuard.EQUIVALENCE_PRINCIPLE

    def test_references_actual_schema_fields(self):
        for field_name in (
            "final_verdict",
            "fetch_status",
            "verdict",
            "records",
            "independent_domain_count",
            "duplicate_domain_count",
            "failed_source_count",
            "self_reported_count",
        ):
            self.assertIn(field_name, self.principle)

    def test_states_final_verdict_must_match_exactly(self):
        self.assertIn("exact same value", self.principle)

    def test_does_not_require_byte_identical_json(self):
        self.assertIn("do NOT affect equivalence", self.principle)

    def test_all_fixed_vocabularies_are_tuples_of_strings(self):
        for vocab in (
            ScamSiteGuard.EVIDENCE_VERDICTS,
            ScamSiteGuard.FETCH_STATUSES,
            ScamSiteGuard.FINAL_VERDICTS,
        ):
            self.assertIsInstance(vocab, tuple)
            for item in vocab:
                self.assertIsInstance(item, str)

    def test_no_overlap_between_vocabularies(self):
        # Sanity check: the fixed vocabularies should be disjoint sets
        # of strings, so a comparator (or a test) can never confuse
        # e.g. a fetch_status value for a final_verdict value.
        all_vocabs = [
            set(ScamSiteGuard.EVIDENCE_VERDICTS),
            set(ScamSiteGuard.FETCH_STATUSES),
            set(ScamSiteGuard.FINAL_VERDICTS),
        ]
        for i in range(len(all_vocabs)):
            for j in range(i + 1, len(all_vocabs)):
                self.assertEqual(all_vocabs[i] & all_vocabs[j], set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
