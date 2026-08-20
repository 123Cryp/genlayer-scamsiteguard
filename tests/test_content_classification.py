"""
Tests for `_classify_content` - the deterministic, pre-LLM content
usability check applied to every successfully-fetched evidence page.
"""

import unittest

from tests._bootstrap import make_contract

_helper = make_contract()

GOOD_CONTENT = (
    "This online store has been the subject of numerous consumer "
    "complaints alleging that orders are never shipped after payment "
    "is collected. Several independent reviewers report similar "
    "experiences over the past year, describing unresponsive customer "
    "service and refusal to issue refunds."
)


class TestClassifyContent(unittest.TestCase):
    def test_none_content_is_empty(self):
        status, usable = _helper._classify_content(None)
        self.assertEqual(status, "empty")
        self.assertFalse(usable)

    def test_empty_string_is_empty(self):
        status, usable = _helper._classify_content("")
        self.assertEqual(status, "empty")
        self.assertFalse(usable)

    def test_whitespace_only_is_empty(self):
        status, usable = _helper._classify_content("   \n\t  ")
        self.assertEqual(status, "empty")
        self.assertFalse(usable)

    def test_too_short_is_empty(self):
        status, usable = _helper._classify_content("Scam site.")
        self.assertEqual(status, "empty")
        self.assertFalse(usable)

    def test_too_few_words_is_empty(self):
        # Long enough in raw character count (>=40) but fewer than 8
        # words - must fail the word-count check specifically, not
        # the length check.
        text = "supercalifragilisticexpialidocious " * 3
        self.assertGreaterEqual(len(text.strip()), 40)
        self.assertLess(len(text.split()), 8)
        status, usable = _helper._classify_content(text)
        self.assertEqual(status, "empty")
        self.assertFalse(usable)

    def test_low_printable_ratio_is_malformed(self):
        garbage = "\x00\x01\x02\x03\x04\x05" * 20 + " word word word word word word word word"
        status, usable = _helper._classify_content(garbage)
        self.assertEqual(status, "malformed")
        self.assertFalse(usable)

    def test_low_alpha_ratio_is_malformed(self):
        numeric = "12345 67890 " * 20
        status, usable = _helper._classify_content(numeric)
        self.assertEqual(status, "malformed")
        self.assertFalse(usable)

    def test_low_character_diversity_is_malformed(self):
        repeated = "aaaa bbbb aaaa bbbb aaaa bbbb aaaa bbbb aaaa bbbb " * 4
        status, usable = _helper._classify_content(repeated)
        self.assertEqual(status, "malformed")
        self.assertFalse(usable)

    def test_captcha_boilerplate_is_empty(self):
        captcha = "Just a moment... Checking your browser before accessing the site. Please enable javascript and cookies."
        status, usable = _helper._classify_content(captcha)
        self.assertEqual(status, "empty")
        self.assertFalse(usable)

    def test_error_page_boilerplate_is_empty(self):
        error_page = "404 not found. The page you are looking for does not exist on this server."
        status, usable = _helper._classify_content(error_page)
        self.assertEqual(status, "empty")
        self.assertFalse(usable)

    def test_good_content_is_ok(self):
        status, usable = _helper._classify_content(GOOD_CONTENT)
        self.assertEqual(status, "ok")
        self.assertTrue(usable)

    def test_long_legitimate_review_content_is_ok(self):
        review = (
            "I ordered a laptop from this site three weeks ago and paid "
            "with a wire transfer as instructed. The tracking number "
            "provided never resolved to a valid shipment, and the "
            "customer support email bounced. I have since found several "
            "other reports online describing the exact same pattern."
        )
        status, usable = _helper._classify_content(review)
        self.assertEqual(status, "ok")
        self.assertTrue(usable)

    def test_does_not_false_positive_on_legitimate_short_technical_text(self):
        # A borderline-length but genuinely coherent piece of content
        # should not be misclassified just because it's compact.
        text = (
            "Domain registered 2019, WHOIS privacy enabled, SSL "
            "certificate issued last month, hosting provider changed "
            "twice in the past six months according to public records."
        )
        status, usable = _helper._classify_content(text)
        self.assertEqual(status, "ok")
        self.assertTrue(usable)


if __name__ == "__main__":
    unittest.main(verbosity=2)
