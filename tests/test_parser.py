"""
Tests for `_parse_evidence_verdict` - the deterministic mapping from
a raw LLM response string to one of the fixed EVIDENCE_VERDICTS.
"""

import unittest

from tests._bootstrap import make_contract

_helper = make_contract()


class TestParseEvidenceVerdict(unittest.TestCase):
    def test_exact_match_scam(self):
        self.assertEqual(_helper._parse_evidence_verdict("IndicatesScam"), "IndicatesScam")

    def test_exact_match_legitimate(self):
        self.assertEqual(
            _helper._parse_evidence_verdict("IndicatesLegitimate"), "IndicatesLegitimate"
        )

    def test_exact_match_unclear(self):
        self.assertEqual(_helper._parse_evidence_verdict("Unclear"), "Unclear")

    def test_case_insensitive_match(self):
        self.assertEqual(_helper._parse_evidence_verdict("indicatesscam"), "IndicatesScam")
        self.assertEqual(_helper._parse_evidence_verdict("INDICATESLEGITIMATE"), "IndicatesLegitimate")

    def test_whitespace_tolerance(self):
        self.assertEqual(_helper._parse_evidence_verdict("  IndicatesScam  \n"), "IndicatesScam")

    def test_trailing_punctuation_stripped(self):
        self.assertEqual(_helper._parse_evidence_verdict("IndicatesScam."), "IndicatesScam")
        self.assertEqual(_helper._parse_evidence_verdict('"IndicatesScam"'), "IndicatesScam")

    def test_multiline_response_scans_all_lines(self):
        raw = "Here is my analysis:\nIndicatesScam\nBased on the complaints described."
        self.assertEqual(_helper._parse_evidence_verdict(raw), "IndicatesScam")

    def test_empty_string_defaults_to_unclear(self):
        self.assertEqual(_helper._parse_evidence_verdict(""), "Unclear")

    def test_none_like_defaults_to_unclear(self):
        self.assertEqual(_helper._parse_evidence_verdict(None), "Unclear")

    def test_garbage_response_defaults_to_unclear(self):
        self.assertEqual(
            _helper._parse_evidence_verdict("I cannot determine this."), "Unclear"
        )

    def test_off_vocabulary_word_defaults_to_unclear(self):
        self.assertEqual(_helper._parse_evidence_verdict("Fraudulent"), "Unclear")

    def test_substring_false_positive_guard(self):
        # "IndicatesScam" appearing as a SUBSTRING inside a longer,
        # unrelated sentence must NOT match - only a line that IS
        # (after trimming) exactly one of the fixed vocabulary words.
        raw = "This does not mean IndicatesScamwithoutspaceafterword is the answer"
        self.assertEqual(_helper._parse_evidence_verdict(raw), "Unclear")

    def test_first_matching_line_wins_when_multiple_present(self):
        raw = "IndicatesScam\nIndicatesLegitimate"
        self.assertEqual(_helper._parse_evidence_verdict(raw), "IndicatesScam")


if __name__ == "__main__":
    unittest.main(verbosity=2)
