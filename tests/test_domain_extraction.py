"""
Tests for `_extract_domain`, `_registrable_domain`, and
`_normalize_target_domain` - the pure, deterministic domain-parsing
helpers this contract's self-report/duplicate detection depends on.
"""

import unittest

from tests._bootstrap import make_contract

_helper = make_contract()


class TestExtractDomain(unittest.TestCase):
    def test_https_url(self):
        self.assertEqual(
            _helper._extract_domain("https://example.com/page"), "example.com"
        )

    def test_http_url(self):
        self.assertEqual(
            _helper._extract_domain("http://example.com/page"), "example.com"
        )

    def test_missing_scheme_is_invalid(self):
        self.assertEqual(_helper._extract_domain("example.com/page"), "")

    def test_ftp_scheme_is_invalid(self):
        self.assertEqual(_helper._extract_domain("ftp://example.com/page"), "")

    def test_query_and_fragment_stripped(self):
        self.assertEqual(
            _helper._extract_domain("https://example.com/page?x=1#y"),
            "example.com",
        )

    def test_userinfo_stripped(self):
        self.assertEqual(
            _helper._extract_domain("https://user:pass@example.com/page"),
            "example.com",
        )

    def test_port_stripped(self):
        self.assertEqual(
            _helper._extract_domain("https://example.com:8443/page"), "example.com"
        )

    def test_trailing_root_dot_stripped(self):
        self.assertEqual(
            _helper._extract_domain("https://example.com./page"), "example.com"
        )

    def test_ipv6_literal(self):
        self.assertEqual(
            _helper._extract_domain("https://[::1]:8080/page"), "::1"
        )

    def test_malformed_ipv6_bracket_is_invalid(self):
        self.assertEqual(_helper._extract_domain("https://[::1:8080/page"), "")

    def test_empty_string_is_invalid(self):
        self.assertEqual(_helper._extract_domain(""), "")

    def test_scheme_only_is_invalid(self):
        self.assertEqual(_helper._extract_domain("https://"), "")

    def test_url_exceeding_max_length_is_invalid(self):
        too_long = "https://example.com/" + ("a" * 2049)
        self.assertEqual(_helper._extract_domain(too_long), "")

    # --- Subdomain-independence: the four required cases ---

    def test_subdomain_reduces_to_registrable_domain(self):
        self.assertEqual(
            _helper._extract_domain("https://news.example.com/x"), "example.com"
        )

    def test_www_subdomain_reduces_to_registrable_domain(self):
        self.assertEqual(
            _helper._extract_domain("https://www.example.com/x"), "example.com"
        )

    def test_different_subdomains_reduce_to_same_domain(self):
        a = _helper._extract_domain("https://mirror1.example.com/x")
        b = _helper._extract_domain("https://mirror2.example.com/x")
        self.assertEqual(a, b)

    def test_bare_domain_without_subdomain_unchanged(self):
        self.assertEqual(
            _helper._extract_domain("https://example.com/x"), "example.com"
        )


class TestRegistrableDomain(unittest.TestCase):
    def test_multi_part_suffix_keeps_three_labels(self):
        self.assertEqual(_helper._registrable_domain("news.bbc.co.uk"), "bbc.co.uk")

    def test_generic_tld_keeps_two_labels(self):
        self.assertEqual(_helper._registrable_domain("news.example.com"), "example.com")

    def test_single_label_host_unchanged(self):
        self.assertEqual(_helper._registrable_domain("localhost"), "localhost")

    def test_ipv4_host_unchanged(self):
        self.assertEqual(_helper._registrable_domain("192.168.0.1"), "192.168.0.1")

    def test_bare_two_label_domain_unchanged(self):
        self.assertEqual(_helper._registrable_domain("example.com"), "example.com")

    def test_deeply_nested_subdomain(self):
        self.assertEqual(
            _helper._registrable_domain("a.b.c.d.example.com"), "example.com"
        )

    def test_com_au_suffix(self):
        self.assertEqual(_helper._registrable_domain("shop.example.com.au"), "example.com.au")


class TestNormalizeTargetDomain(unittest.TestCase):
    """
    Pure function: a caller-supplied `target_domain` -> the same
    approximate registrable-domain form `_extract_domain` computes
    for evidence URLs. This is what lets `_annotate_evidence` compare
    "the domain an evidence URL actually resolved to" against "the
    domain under suspicion" using one consistent representation.
    """

    def test_bare_domain_is_normalized(self):
        self.assertEqual(
            _helper._normalize_target_domain("scam-site.example"),
            "scam-site.example",
        )

    def test_bare_domain_with_www_normalizes_same_as_without(self):
        self.assertEqual(
            _helper._normalize_target_domain("www.scam-site.example"),
            "scam-site.example",
        )

    def test_full_url_normalizes_to_same_domain_as_bare_form(self):
        self.assertEqual(
            _helper._normalize_target_domain("https://scam-site.example/shop"),
            "scam-site.example",
        )

    def test_uppercase_and_whitespace_are_normalized(self):
        self.assertEqual(
            _helper._normalize_target_domain("  Scam-Site.EXAMPLE  "),
            "scam-site.example",
        )

    def test_multi_part_suffix_domain_is_normalized_consistently(self):
        self.assertEqual(
            _helper._normalize_target_domain("shop.bbc.co.uk"), "bbc.co.uk"
        )

    def test_empty_string_is_invalid(self):
        self.assertEqual(_helper._normalize_target_domain(""), "")
        self.assertEqual(_helper._normalize_target_domain("   "), "")

    def test_overlong_entry_is_invalid(self):
        too_long = "a" * 254 + ".com"
        self.assertEqual(_helper._normalize_target_domain(too_long), "")

    def test_unparseable_entry_is_invalid(self):
        self.assertEqual(_helper._normalize_target_domain("ftp://x.com"), "")

    def test_subdomain_of_target_matches_same_normalized_form(self):
        # This is the property _annotate_evidence's self-report
        # detection depends on: a target declared as "scam.example"
        # and an evidence URL on "www.scam.example" must normalize to
        # the SAME domain string, or the self-report check would be
        # trivially bypassed with a subdomain.
        target = _helper._normalize_target_domain("scam.example")
        evidence_domain = _helper._extract_domain("https://www.scam.example/proof")
        self.assertEqual(target, evidence_domain)


if __name__ == "__main__":
    unittest.main(verbosity=2)
