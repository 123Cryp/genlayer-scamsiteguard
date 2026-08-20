"""
Tests for `_aggregate` - the deterministic decision rule that turns
per-evidence verdicts into one final verdict. This is where the
core anti-self-vouching design (see contract.py's class docstring)
is actually enforced.
"""

import unittest

from tests._bootstrap import ScamSiteGuard, make_contract

_helper = make_contract()


class TestAggregation(unittest.TestCase):
    def _rec(
        self,
        verdict,
        domain,
        status="ok",
        dup=False,
        low_cred=False,
        self_reported=False,
    ):
        return {
            "url": f"https://{domain}/a",
            "domain": domain,
            "is_duplicate_domain": dup,
            "is_low_credibility": low_cred,
            "is_self_reported": self_reported,
            "fetch_status": status,
            "verdict": verdict,
        }

    # --- Insufficient evidence ---

    def test_single_source_is_insufficient(self):
        records = [self._rec("IndicatesScam", "a.com")]
        self.assertEqual(_helper._aggregate(records), "InsufficientEvidence")

    def test_no_records_is_insufficient(self):
        self.assertEqual(_helper._aggregate([]), "InsufficientEvidence")

    def test_all_failed_fetches_is_insufficient(self):
        records = [
            self._rec("NoEvidence", "a.com", status="timeout"),
            self._rec("NoEvidence", "b.com", status="inaccessible"),
        ]
        self.assertEqual(_helper._aggregate(records), "InsufficientEvidence")

    # --- LikelyScam / LikelyLegitimate ---

    def test_two_independent_scam_indicators_yields_likely_scam(self):
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("IndicatesScam", "b.com"),
        ]
        self.assertEqual(_helper._aggregate(records), "LikelyScam")

    def test_two_independent_legit_indicators_yields_likely_legitimate(self):
        records = [
            self._rec("IndicatesLegitimate", "a.com"),
            self._rec("IndicatesLegitimate", "b.com"),
        ]
        self.assertEqual(_helper._aggregate(records), "LikelyLegitimate")

    def test_majority_with_dissent_still_resolves(self):
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("IndicatesScam", "b.com"),
            self._rec("IndicatesLegitimate", "c.com"),
        ]
        self.assertEqual(_helper._aggregate(records), "LikelyScam")

    # --- Disputed / Unverified ---

    def test_tied_scam_and_legit_is_disputed(self):
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("IndicatesLegitimate", "b.com"),
        ]
        self.assertEqual(_helper._aggregate(records), "Disputed")

    def test_mostly_unclear_yields_unverified(self):
        records = [
            self._rec("Unclear", "a.com"),
            self._rec("Unclear", "b.com"),
        ]
        self.assertEqual(_helper._aggregate(records), "Unverified")

    def test_one_scam_one_unclear_is_insufficient(self):
        # Only 1 eligible domain actually casts a directional
        # verdict; Unclear doesn't count toward scam_count or
        # legit_count, so this can't reach LikelyScam (needs >=2).
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("Unclear", "b.com"),
        ]
        self.assertEqual(_helper._aggregate(records), "Unverified")

    # --- Exclusion gating: duplicate domain ---

    def test_duplicate_domain_not_counted_as_corroboration(self):
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("IndicatesScam", "a.com", dup=True),
        ]
        self.assertEqual(_helper._aggregate(records), "InsufficientEvidence")

    # --- Exclusion gating: low credibility ---

    def test_low_credibility_domain_not_counted_as_corroboration(self):
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("IndicatesScam", "b.com", low_cred=True),
        ]
        self.assertEqual(_helper._aggregate(records), "InsufficientEvidence")

    # --- Exclusion gating: self-reported (the core novel mechanic) ---

    def test_self_reported_evidence_excluded_even_if_only_source(self):
        # The target's own "we are 100% legitimate" page must never,
        # by itself, be enough to reach LikelyLegitimate.
        records = [
            self._rec("IndicatesLegitimate", "target.example", self_reported=True),
        ]
        self.assertEqual(_helper._aggregate(records), "InsufficientEvidence")

    def test_self_reported_plus_one_real_source_still_insufficient(self):
        # Even with one genuine third-party source, a single
        # self-reported page cannot make up the second independent
        # domain required.
        records = [
            self._rec("IndicatesLegitimate", "target.example", self_reported=True),
            self._rec("IndicatesLegitimate", "reviews.example"),
        ]
        self.assertEqual(_helper._aggregate(records), "InsufficientEvidence")

    def test_self_reported_excluded_regardless_of_its_own_verdict(self):
        # Self-reported evidence is excluded structurally, not
        # because the LLM judged it unfavorably - even a
        # self-reported page that (unusually) says "this is a scam"
        # must still be excluded, since the exclusion is about
        # independence, not content.
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("IndicatesScam", "b.com"),
            self._rec("IndicatesScam", "target.example", self_reported=True),
        ]
        result = _helper._aggregate(records)
        self.assertEqual(result, "LikelyScam")
        # And removing the two real sources, only the self-reported
        # one remains - must NOT be enough on its own.
        records_only_self = [
            self._rec("IndicatesScam", "target.example", self_reported=True),
        ]
        self.assertEqual(_helper._aggregate(records_only_self), "InsufficientEvidence")

    def test_two_real_sources_plus_self_report_still_verifies(self):
        # A self-reported source among otherwise-sufficient
        # third-party corroboration doesn't poison the result - it's
        # simply excluded, and the remaining two independent sources
        # are enough on their own.
        records = [
            self._rec("IndicatesLegitimate", "a.com"),
            self._rec("IndicatesLegitimate", "b.com"),
            self._rec("IndicatesLegitimate", "target.example", self_reported=True),
        ]
        self.assertEqual(_helper._aggregate(records), "LikelyLegitimate")

    def test_self_reported_and_duplicate_and_low_cred_all_stack_correctly(self):
        # Three different exclusion reasons at once, plus two
        # genuinely eligible sources - only the two eligible ones
        # should count.
        records = [
            self._rec("IndicatesScam", "a.com"),
            self._rec("IndicatesScam", "b.com"),
            self._rec("IndicatesScam", "a.com", dup=True),
            self._rec("IndicatesLegitimate", "theonion.com", low_cred=True),
            self._rec("IndicatesLegitimate", "target.example", self_reported=True),
        ]
        self.assertEqual(_helper._aggregate(records), "LikelyScam")


class TestAggregationRequiresAllKeys(unittest.TestCase):
    """
    Unlike TruthBeacon v2.8's optional add-on flags, `is_self_reported`
    is a REQUIRED field this contract itself always produces for
    every record - there is no legacy pre-self-report record shape to
    stay compatible with, since this contract has no version before
    this mechanic existed. A record missing the key is not a valid
    input to `_aggregate` and should fail loudly rather than silently
    default to "eligible", which would defeat the whole point of the
    exclusion.
    """

    def test_missing_self_reported_key_raises(self):
        records = [
            {
                "url": "https://a.com/x",
                "domain": "a.com",
                "is_duplicate_domain": False,
                "is_low_credibility": False,
                "fetch_status": "ok",
                "verdict": "IndicatesScam",
                # is_self_reported deliberately omitted
            },
            {
                "url": "https://b.com/x",
                "domain": "b.com",
                "is_duplicate_domain": False,
                "is_low_credibility": False,
                "is_self_reported": False,
                "fetch_status": "ok",
                "verdict": "IndicatesScam",
            },
        ]
        with self.assertRaises(KeyError):
            _helper._aggregate(records)


if __name__ == "__main__":
    unittest.main(verbosity=2)
