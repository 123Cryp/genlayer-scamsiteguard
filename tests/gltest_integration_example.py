"""
⚠️ EXAMPLE / SKETCH ONLY — NOT YET VALIDATED AGAINST A LIVE GENLAYER
ENVIRONMENT. Do not treat this file as a verified, passing test
suite until it has actually been run.

Live GenLayer integration test sketch for ScamSiteGuard, using the
official `gltest` framework (see: https://pypi.org/project/genlayer-test/).

Unlike tests/test_*.py (which run fully offline against a stub SDK
and ARE actually executed and passing - 128/128 tests - as part of
this submission), THIS file has never been run. There is no GenLayer
Studio or local node available in the environment this contract was
developed in, so these tests could not be executed or confirmed to
pass. The exact `gltest` API surface used below
(`get_contract_factory(...)`, `factory.deploy(...)`, the
`mock_web_responses=` / `mock_llm_responses=` keyword arguments, and
the `MockedLLMResponse` substring-matching behavior) is based on
published `gltest` documentation but has not been confirmed against
a real installed version of the package, and may need small
adjustments (parameter names, mock dict shape, etc.) before it will
actually run.

Use this file as a starting point for writing real integration tests
once you have a GenLayer Studio/testnet available - validate it
there, fix whatever doesn't match your `gltest` version, and only
then treat it as a trustworthy part of the test suite.

It sketches the core scenarios this contract is built around:
successful scam verdict, successful legitimate verdict, conflicting
evidence, duplicate domains, self-reported evidence (the core
anti-self-vouching mechanic), failed fetches, and an
all-self-reported upfront-rejection scenario, using `gltest`'s Mock
Web Response and Mocked LLM Response systems so these tests would be
deterministic and not depend on real websites being up, once
validated.

Run with a GenLayer Studio instance running:
    pip install genlayer-test --break-system-packages
    gltest test tests/gltest_integration_example.py

This file is NOT executed by the offline unit test suite and is NOT
part of the "128 tests passing" claim made elsewhere in this project.
"""

import json

import pytest
from gltest import get_contract_factory
from gltest.types import MockedLLMResponse, MockedWebResponse


TARGET = "scam-site.example"

GOOD_URLS = [
    "https://reviews.example/scam-site",
    "https://consumerwatch.example/scam-site",
    "https://forum.example/scam-site-thread",
]


@pytest.fixture
def scam_site_guard():
    factory = get_contract_factory("ScamSiteGuard")
    return factory.deploy(args=[])


def test_successful_scam_verdict(scam_site_guard):
    """Three independent, agreeing sources -> 'LikelyScam'."""
    mock_web = {
        url: MockedWebResponse(
            status_code=200,
            body="Multiple customers report paying and never receiving their orders.",
        )
        for url in GOOD_URLS
    }
    mock_llm: MockedLLMResponse = {"nondet_exec_prompt": {"default": "IndicatesScam"}}

    check_id = scam_site_guard.submit_check(
        args=[TARGET, GOOD_URLS],
        mock_web_responses=mock_web,
        mock_llm_responses=mock_llm,
    )
    result = json.loads(scam_site_guard.get_check(args=[check_id]))
    assert result["final_verdict"] == "LikelyScam"
    assert result["independent_domain_count"] == 3


def test_successful_legitimate_verdict(scam_site_guard):
    """Three independent, agreeing sources -> 'LikelyLegitimate'."""
    mock_web = {
        url: MockedWebResponse(
            status_code=200,
            body="This retailer has consistently fast shipping and responsive support.",
        )
        for url in GOOD_URLS
    }
    mock_llm: MockedLLMResponse = {
        "nondet_exec_prompt": {"default": "IndicatesLegitimate"}
    }

    check_id = scam_site_guard.submit_check(
        args=["goodstore.example", GOOD_URLS],
        mock_web_responses=mock_web,
        mock_llm_responses=mock_llm,
    )
    result = json.loads(scam_site_guard.get_check(args=[check_id]))
    assert result["final_verdict"] == "LikelyLegitimate"


def test_conflicting_evidence(scam_site_guard):
    """Independent sources disagree -> 'Disputed'."""
    urls = [
        "https://prosource.example/story",
        "https://consource.example/story",
        "https://neutralsource.example/story",
    ]
    mock_web = {
        urls[0]: MockedWebResponse(status_code=200, body="Evidence strongly confirms the site is a scam."),
        urls[1]: MockedWebResponse(status_code=200, body="Evidence strongly confirms the site is legitimate."),
        urls[2]: MockedWebResponse(status_code=200, body="Evidence is mixed and inconclusive either way."),
    }
    # gltest's mock LLM system pattern-matches on the constructed user
    # message, so distinct evidence content routes to distinct verdicts.
    mock_llm: MockedLLMResponse = {
        "nondet_exec_prompt": {
            "is a scam": "IndicatesScam",
            "is legitimate": "IndicatesLegitimate",
            "mixed and inconclusive": "Unclear",
        }
    }

    check_id = scam_site_guard.submit_check(
        args=["ambiguous-site.example", urls],
        mock_web_responses=mock_web,
        mock_llm_responses=mock_llm,
    )
    result = json.loads(scam_site_guard.get_check(args=[check_id]))
    assert result["final_verdict"] == "Disputed"


def test_duplicate_domains_not_independent(scam_site_guard):
    """Two URLs on the same domain only count as one independent source."""
    urls = [
        "https://reviews.example/story",
        "https://reviews.example/story-mirror",
        "https://forum.example/thread",
    ]
    mock_web = {
        url: MockedWebResponse(status_code=200, body="Detailed evidence describing the scam pattern in depth.")
        for url in urls
    }
    mock_llm: MockedLLMResponse = {"nondet_exec_prompt": {"default": "IndicatesScam"}}

    check_id = scam_site_guard.submit_check(
        args=[TARGET, urls],
        mock_web_responses=mock_web,
        mock_llm_responses=mock_llm,
    )
    result = json.loads(scam_site_guard.get_check(args=[check_id]))
    assert result["duplicate_domain_count"] == 1
    assert result["final_verdict"] == "LikelyScam"  # from the 2 non-duplicate domains


def test_self_reported_evidence_excluded(scam_site_guard):
    """
    The target's own page vouching for itself must be fetched and
    judged, but categorically excluded from corroboration - the core
    anti-self-vouching mechanic this contract exists to enforce.
    """
    urls = [
        "https://scam-site.example/we-are-legit",
        "https://reviews.example/scam-site-review",
        "https://forum.example/scam-site-thread",
    ]
    mock_web = {
        urls[0]: MockedWebResponse(status_code=200, body="We are a fully legitimate, verified business."),
        urls[1]: MockedWebResponse(status_code=200, body="Numerous customers report non-delivery of orders."),
        urls[2]: MockedWebResponse(status_code=200, body="A forum thread documenting repeated scam complaints."),
    }
    mock_llm: MockedLLMResponse = {
        "nondet_exec_prompt": {
            "fully legitimate": "IndicatesLegitimate",
            "non-delivery": "IndicatesScam",
            "scam complaints": "IndicatesScam",
        }
    }

    check_id = scam_site_guard.submit_check(
        args=["scam-site.example", urls],
        mock_web_responses=mock_web,
        mock_llm_responses=mock_llm,
    )
    result = json.loads(scam_site_guard.get_check(args=[check_id]))
    assert result["self_reported_count"] == 1
    self_reported = next(
        e for e in result["evidence"] if e["domain"] == "scam-site.example"
    )
    assert self_reported["is_self_reported"] is True
    assert self_reported["fetch_status"] == "ok"  # still fetched and judged
    assert result["final_verdict"] == "LikelyScam"  # self-report couldn't save it


def test_failed_fetch_recorded_not_dropped(scam_site_guard):
    """A page that fails to fetch must be recorded, not silently omitted."""
    urls = [
        "https://reviews.example/story",
        "https://forum.example/thread",
        "https://unreachable.example/gone",
    ]
    mock_web = {
        urls[0]: MockedWebResponse(status_code=200, body="Detailed evidence describing the scam pattern in depth."),
        urls[1]: MockedWebResponse(status_code=200, body="Detailed evidence describing the scam pattern in depth."),
        urls[2]: MockedWebResponse(status_code=500, body=""),
    }
    mock_llm: MockedLLMResponse = {"nondet_exec_prompt": {"default": "IndicatesScam"}}

    check_id = scam_site_guard.submit_check(
        args=[TARGET, urls],
        mock_web_responses=mock_web,
        mock_llm_responses=mock_llm,
    )
    result = json.loads(scam_site_guard.get_check(args=[check_id]))
    assert result["failed_source_count"] == 1
    failed = next(e for e in result["evidence"] if e["domain"] == "unreachable.example")
    assert failed["fetch_status"] in ("inaccessible", "timeout", "empty", "malformed")


def test_all_self_reported_rejected_upfront(scam_site_guard):
    """
    All evidence hosted on the target's own domain can never satisfy
    MIN_INDEPENDENT_DOMAINS - submit_check should reject this before
    spending any fetch/LLM cost, not merely resolve to
    InsufficientEvidence after paying for it.
    """
    urls = [
        "https://scam-site.example/page1",
        "https://www.scam-site.example/page2",
        "https://shop.scam-site.example/page3",
    ]
    with pytest.raises(Exception):
        scam_site_guard.submit_check(
            args=["scam-site.example", urls],
            mock_web_responses={},
            mock_llm_responses={"nondet_exec_prompt": {"default": "IndicatesLegitimate"}},
        )
