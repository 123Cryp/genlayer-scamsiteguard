"""
Tests for `get_check`, `get_verdict`, `total_checks`, and multi-check
storage isolation.
"""

import json
import unittest
from unittest.mock import patch

from tests._bootstrap import ScamSiteGuard, gl, make_contract


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.contract = make_contract()

    def _submit(self, target_domain, urls, verdict_word):
        def fetch(url, mode="text"):
            return "Detailed content about the target site's practices. " * 5

        def prompt(p, response_format="text"):
            return verdict_word

        with patch.object(gl.nondet.web, "render", side_effect=fetch), patch.object(
            gl.nondet, "exec_prompt", side_effect=prompt
        ):
            return self.contract.submit_check(target_domain, urls)

    def test_total_checks_starts_at_zero(self):
        self.assertEqual(self.contract.total_checks(), 0)

    def test_get_check_unknown_id_raises(self):
        with self.assertRaises(gl.vm.UserError):
            self.contract.get_check("999")

    def test_get_verdict_unknown_id_raises(self):
        with self.assertRaises(gl.vm.UserError):
            self.contract.get_verdict("999")

    def test_submit_then_get_check_roundtrip(self):
        urls = ["https://a.example/1", "https://b.example/2", "https://c.example/3"]
        check_id = self._submit("scam.example", urls, "IndicatesScam")
        record = json.loads(self.contract.get_check(check_id))
        self.assertEqual(record["check_id"], check_id)
        self.assertEqual(record["target_domain"], "scam.example")
        self.assertEqual(record["final_verdict"], "LikelyScam")

    def test_get_verdict_matches_get_check(self):
        urls = ["https://a.example/1", "https://b.example/2", "https://c.example/3"]
        check_id = self._submit("legit.example", urls, "IndicatesLegitimate")
        full = json.loads(self.contract.get_check(check_id))
        verdict_only = self.contract.get_verdict(check_id)
        self.assertEqual(full["final_verdict"], verdict_only)

    def test_multiple_checks_remain_independently_retrievable(self):
        urls = ["https://a.example/1", "https://b.example/2", "https://c.example/3"]
        id1 = self._submit("site-one.example", urls, "IndicatesScam")
        id2 = self._submit("site-two.example", urls, "IndicatesLegitimate")
        id3 = self._submit("site-three.example", urls, "Unclear")

        self.assertEqual(self.contract.total_checks(), 3)

        rec1 = json.loads(self.contract.get_check(id1))
        rec2 = json.loads(self.contract.get_check(id2))
        rec3 = json.loads(self.contract.get_check(id3))

        self.assertEqual(rec1["target_domain"], "site-one.example")
        self.assertEqual(rec2["target_domain"], "site-two.example")
        self.assertEqual(rec3["target_domain"], "site-three.example")
        self.assertEqual(rec1["final_verdict"], "LikelyScam")
        self.assertEqual(rec2["final_verdict"], "LikelyLegitimate")
        self.assertEqual(rec3["final_verdict"], "Unverified")

    def test_check_ids_are_sequential_strings(self):
        urls = ["https://a.example/1", "https://b.example/2", "https://c.example/3"]
        id1 = self._submit("a.example", urls, "IndicatesScam")
        id2 = self._submit("b.example", urls, "IndicatesScam")
        self.assertEqual(id1, "0")
        self.assertEqual(id2, "1")

    def test_get_check_returns_valid_json_string(self):
        urls = ["https://a.example/1", "https://b.example/2", "https://c.example/3"]
        check_id = self._submit("scam.example", urls, "IndicatesScam")
        raw = self.contract.get_check(check_id)
        self.assertIsInstance(raw, str)
        parsed = json.loads(raw)  # must not raise
        self.assertIn("evidence", parsed)

    def test_stored_record_contains_full_evidence_trail(self):
        urls = ["https://a.example/1", "https://b.example/2", "https://c.example/3"]
        check_id = self._submit("scam.example", urls, "IndicatesScam")
        record = json.loads(self.contract.get_check(check_id))
        self.assertEqual(len(record["evidence"]), 3)
        for e in record["evidence"]:
            for field in (
                "url",
                "domain",
                "is_duplicate_domain",
                "is_low_credibility",
                "is_self_reported",
                "fetch_status",
                "verdict",
            ):
                self.assertIn(field, e)


if __name__ == "__main__":
    unittest.main(verbosity=2)
