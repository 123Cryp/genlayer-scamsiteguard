# Changelog

## v1.0 — Initial Submission (Current)

First submission of ScamSiteGuard: a corroborated scam-website verification Intelligent Contract with structural, self-vouching-resistant evidence corroboration.

**Core mechanism:**
- `submit_check(target_domain, evidence_urls)`: caller submits a domain under suspicion together with 3–6 candidate evidence URLs.
- Every evidence URL is independently fetched (`gl.nondet.web.render`) and judged by an LLM (`gl.nondet.exec_prompt`) inside a single `gl.eq_principle.prompt_comparative` consensus round.
- Deterministic pre-flight annotation (`_annotate_evidence`) computes, for every evidence URL before any network access: registrable domain, duplicate-domain status, low-credibility-denylist status, and — the headline novel mechanic — `is_self_reported` status (whether the evidence is hosted on the target's own domain or a subdomain of it).
- `_aggregate` combines per-evidence verdicts into one final verdict (`LikelyScam`/`LikelyLegitimate`/`Disputed`/`Unverified`/`InsufficientEvidence`), excluding duplicate, low-credibility, AND self-reported evidence from corroboration.
- Full auditable evidence trail (every submitted URL, its provenance flags, fetch status, and verdict — including excluded evidence, never silently dropped) persisted on-chain via `get_check`.

**Design rationale:** self-report exclusion is implemented as a deterministic domain-match check, not an LLM judgment call — see [DESIGN_DECISIONS.md § 1](DESIGN_DECISIONS.md#1-why-self-reported-exclusion-is-structural-not-llm-judged) for why an LLM-based approach was considered and rejected.

**Testing:**
- 128/128 offline tests passing across 8 files (`test_domain_extraction.py`, `test_content_classification.py`, `test_aggregation.py`, `test_parser.py`, `test_prompt_and_consensus.py`, `test_input_validation.py`, `test_end_to_end.py`, `test_storage.py`).
- An unexecuted `gltest` integration example (`tests/gltest_integration_example.py`), explicitly disclosed as not-yet-validated against a live `gltest` install.

**Live deployment:**
- Deployed to GenLayer Studio: `0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D`.
- 3 successful `submit_check` transactions, all `FINALIZED`: a combined duplicate-domain + fetch-failure demonstration (`InsufficientEvidence`); a dedicated demonstration of the self-reported-evidence exclusion mechanic — the target domain's own Wikipedia page was fetched, judged `IndicatesLegitimate` by the LLM, and correctly excluded from corroboration; and a combined demonstration where a *different* Wikipedia subdomain was simultaneously flagged both `is_duplicate_domain` and `is_self_reported`, confirming the two mechanics share the same domain-reduction logic live. A fourth transaction, deliberately submitting a majority-self-reported evidence set, was correctly rejected by pre-flight validation before any fetch — every validator independently agreed on the identical rollback reason. Full detail: [REVIEWER_GUIDE.md § 4](REVIEWER_GUIDE.md#4-live-transaction-evidence).

**GenVM lint compliance:** every internal helper method (`_extract_domain`, `_registrable_domain`, `_normalize_target_domain`, `_classify_content`, `_annotate_evidence`, `_aggregate`, `_parse_evidence_verdict`, `_build_prompt`) is a plain instance method with `self` as the first parameter — no `@classmethod`/`@staticmethod` anywhere, satisfying GenVM lint rule E022 from the start (a real, previously-hit issue in a companion contract's history — see that project's own changelog for the full story of what happens if this rule is violated).
