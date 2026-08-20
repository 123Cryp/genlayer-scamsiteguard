"""
Tests for `submit_check`'s pre-fetch, deterministic input validation
- everything that must reject BEFORE any gl.nondet.* call is made, so
bad submissions fail fast and cheaply.
"""

import unittest
from unittest.mock import patch

from tests._bootstrap import ScamSiteGuard, gl, make_contract


class TestInputValidation(unittest.TestCase):
    def setUp(self):
        self.c = make_contract()
        self.good_urls = [
            "https://reviews.example/a",
            "https://forum.example/b",
            "https://reports.example/c",
        ]

    def test_empty_target_domain_rejected(self):
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check("", self.good_urls)

    def test_whitespace_only_target_domain_rejected(self):
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check("   ", self.good_urls)

    def test_unparseable_target_domain_rejected(self):
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check("ftp://scam.example", self.good_urls)

    def test_too_few_evidence_urls_rejected(self):
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check("scam.example", self.good_urls[:2])

    def test_zero_evidence_urls_rejected(self):
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check("scam.example", [])

    def test_too_many_evidence_urls_rejected(self):
        too_many = [f"https://site{i}.example/x" for i in range(7)]
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check("scam.example", too_many)

    def test_exactly_min_evidence_urls_accepted(self):
        with patch.object(
            gl.nondet.web, "render", side_effect=lambda *a, **k: "x " * 20
        ), patch.object(gl.nondet, "exec_prompt", side_effect=lambda *a, **k: "Unclear"):
            # Must not raise.
            self.c.submit_check("scam.example", self.good_urls)

    def test_oversized_url_rejected(self):
        too_long_url = "https://a.example/" + ("x" * 2049)
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check(
                "scam.example",
                [too_long_url, "https://b.example/x", "https://c.example/x"],
            )

    def test_insufficient_distinct_domains_rejected(self):
        # 3 URLs but only 1 distinct domain (via subdomains) - fails
        # the pre-flight independence check.
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check(
                "scam.example",
                [
                    "https://a.example/1",
                    "https://www.a.example/2",
                    "https://mirror.a.example/3",
                ],
            )

    def test_all_self_reported_evidence_rejected_upfront(self):
        # All 3 evidence URLs are on the target's own domain - can
        # never reach 2 independent third-party domains, so this
        # should fail fast, before any fetch.
        with self.assertRaises(gl.vm.UserError):
            self.c.submit_check(
                "scam.example",
                [
                    "https://scam.example/1",
                    "https://www.scam.example/2",
                    "https://shop.scam.example/3",
                ],
            )

    def test_error_is_gl_vm_user_error_type(self):
        # SDK-correctness check: must be gl.vm.UserError, not a bare
        # Exception or ValueError.
        try:
            self.c.submit_check("", self.good_urls)
            self.fail("Expected gl.vm.UserError to be raised")
        except gl.vm.UserError:
            pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
