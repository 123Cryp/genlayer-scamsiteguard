# ScamSiteGuard — Project Overview

*A 5-minute summary for judges. For depth, see [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md).*

---

## What It Is

A GenLayer Intelligent Contract that verifies whether a website is likely a scam by requiring **multiple independent, third-party sources** to corroborate — and, critically, by structurally excluding the target site's own self-published content from counting toward that corroboration. Anyone submits a `target_domain` plus 3–6 candidate evidence URLs; GenLayer validators fetch and judge each source with an LLM, reach consensus, and the contract stores a full auditable evidence trail on-chain.

## Why It Exists

Scam-website verification is adversarial in a way generic fact-checking isn't: the entity being evaluated has a direct incentive to make itself look legitimate, and controls content on its own domain completely. A naive "fetch pages, ask an LLM" design can be gamed by the target simply publishing its own favorable page and submitting it as evidence. ScamSiteGuard is built specifically to close that hole — structurally, not by trying to out-argue a motivated actor with a cleverer prompt.

## What Makes It Notable

- **Corroboration, not trust:** requires ≥2 independent, credible, third-party domains to agree before claiming `LikelyScam` or `LikelyLegitimate`. One confident source is never enough.
- **Self-vouching-resistant (the headline mechanic):** any evidence hosted on the target's own domain — or any subdomain of it — is fetched and judged like any other source (nothing hidden), but is deterministically, unconditionally excluded from corroboration in `_aggregate`. This is a domain-identity fact the contract checks directly, not an LLM judgment call that could be argued past.
- **Fails fast on all-self-reported submissions:** if every submitted evidence URL turns out to be on the target's own domain, the contract rejects the call before spending any fetch/LLM cost.
- **Sybil-resistant:** detects when submitted URLs are really the same publisher (subdomains, mirrors) via registrable-domain matching, independent of the self-report check.
- **Honest under uncertainty:** conflicting independent evidence resolves to `Disputed`, not a forced pick; insufficient evidence resolves to `InsufficientEvidence`, not a confident-sounding guess.
- **Consensus-correct:** uses `gl.eq_principle.prompt_comparative`, the SDK-correct primitive for LLM-derived output, never `strict_eq`.
- **Transparent by design:** self-reported, duplicate, and denylisted evidence is still fetched, judged, and persisted in full — never silently dropped, just clearly flagged as excluded and why.

## Proof, Not Just Claims

| | |
|---|---|
| Offline tests | **128/128 passing**, `python3 -m unittest discover -s tests -p "test_*.py"` |
| Live deployment | **Yes** — `0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D` on GenLayer Studio |
| Live transactions | **4** — 3 successful `submit_check` calls (all `FINALIZED`) plus 1 pre-flight rejection (also `FINALIZED`, on the rejection itself) — including a direct exercise of the core self-reported-evidence exclusion mechanic: a target domain's own page fetched, judged `IndicatesLegitimate`, and still correctly excluded from its own verdict; and a combined demonstration of self-report detection stacking correctly with duplicate-domain detection via a different subdomain |
| Core mechanic test coverage | 6+ dedicated offline tests, PLUS 3 live transactions proving the same mechanic on real infrastructure |
| Public verification | https://explorer-studio.genlayer.com/address/0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D |

## The One-Sentence Pitch

*A scam-verification contract that a scam site can't simply talk its own way out of — because its own words don't count as a witness.*

## Where to Go Next

- **Verify the core mechanic in 2 minutes:** [REVIEWER_GUIDE.md § 4](REVIEWER_GUIDE.md#4-live-transaction-evidence) — transaction 2, where the target's own page is fetched, judged favorably, and still correctly excluded
- **See it tested offline too:** `tests/test_aggregation.py`'s `test_self_reported_evidence_excluded_even_if_only_source` and neighboring tests
- **Understand the design:** [ARCHITECTURE.md](ARCHITECTURE.md), [DESIGN_DECISIONS.md § 1](DESIGN_DECISIONS.md#1-why-self-reported-exclusion-is-structural-not-llm-judged)
- **See the threat model:** [SECURITY.md](SECURITY.md)
- **See what's honestly not solved:** [SECURITY.md § 8](SECURITY.md#8-formally-unrelated-second-domain-residual-risk), [ROADMAP.md](ROADMAP.md)
