# ScamSiteGuard — Self-Report-Resistant Scam Website Verification on GenLayer

ScamSiteGuard is a GenLayer Intelligent Contract for decentralized scam-website verification. Anyone submits a `target_domain` (a site they're suspicious of) together with candidate `evidence_urls`; GenLayer's validators independently fetch and judge each piece of evidence, and reach Optimistic Democracy consensus on one deterministic final verdict, stored permanently on-chain with a full, auditable evidence trail.

This contract does not determine absolute truth. It deterministically evaluates whether multiple independent, third-party sources indicate a domain is a scam or legitimate under GenLayer consensus rules. A `LikelyScam` or `LikelyLegitimate` verdict means "enough independent, credible, third-party evidence agreed" — not an infallible statement of objective fact.

**Deployed and exercised live on GenLayer Studio** (see [Live Deployment](#live-deployment) below) — including a direct, on-chain demonstration of the self-reported-evidence exclusion mechanic: a target domain's own page was fetched, judged favorably, and still correctly excluded from its own verdict.

> **The core design problem this contract solves:** a naive "fetch some pages about a site, ask an LLM if they look positive or negative, aggregate" design has an obvious hole — a scam operator can trivially publish their own "Verified Legitimate Business!" page, or a fake glowing review on a copycat site they also control, and if that gets submitted as evidence, it would count toward a favorable verdict despite being entirely self-authored. ScamSiteGuard closes this hole **structurally**, not by trying to out-argue a motivated LLM: any evidence URL whose domain *is* the target domain (or a subdomain of it) is deterministically flagged `is_self_reported` and categorically excluded from corroboration, regardless of what it says. See [Design Rationale](#design-rationale-the-self-vouching-problem) below.

## Documentation Map

| Document | What's in it |
|---|---|
| `README.md` (this file) | Quick start, interface reference, aggregation rule, design rationale |
| `ARCHITECTURE.md` | Component diagram, execution flow, storage/consensus model, why `prompt_comparative` |
| `SECURITY.md` | Full threat model — self-vouching, prompt injection, fake evidence domains, Sybil domains, fetch failures, known limitations |
| `DESIGN_DECISIONS.md` | Every design choice: problem → solution → alternative considered → trade-offs |
| `TESTING.md` | Offline tests, the unexecuted integration example, and live deployment evidence tiers |
| `CHANGELOG.md` | Version history |
| `ROADMAP.md` | What's intentionally out of scope, and why, for each future direction |
| `CONTRIBUTING.md` | How to contribute, and what not to change casually |
| `REVIEWER_GUIDE.md` | Where every claim in this repo can be independently verified |
| `PROJECT_OVERVIEW.md` | 5-minute executive summary |
| `SUBMISSION_CHECKLIST.md` | Pre-submission checklist |
| `tests/README.md` | Test-file-by-test-file coverage index |

## Live Deployment

**Contract address:** `0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D`
**Public explorer (all transactions):** https://explorer-studio.genlayer.com/address/0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D

Deployed and exercised on GenLayer Studio with four live `submit_check` calls, including a direct demonstration of the core self-reported-evidence exclusion mechanic, and a combined demonstration of self-report detection stacking correctly with subdomain-independence:

**Transaction 1 — duplicate-domain + fetch-failure handling** (tx [`0x8e3b64d0560d21fe5b60917a39514f7b33b184e547676afda5082bf0f664f4fb`](https://explorer-studio.genlayer.com/tx/0x8e3b64d0560d21fe5b60917a39514f7b33b184e547676afda5082bf0f664f4fb), **FINALIZED**): `submit_check("scam-electronics-outlet.example", ["https://en.wikipedia.org/wiki/Wikipedia", "https://en.wikipedia.org/wiki/Reliability_of_Wikipedia", "https://www.britannica.com/topic/Wikipedia"])`. Result (`check_id "0"`): both Wikipedia URLs fetched successfully and resolved to `Unclear`, but the second was correctly flagged `is_duplicate_domain: true` (same registrable domain as the first) and excluded from corroboration; `britannica.com` failed to fetch (`inaccessible`). With only 1 eligible domain remaining, `final_verdict: "InsufficientEvidence"` — an honest, conservative result.

**Transaction 2 — pre-flight rejection** (tx [`0x0ff90143ff9db110876cdbb4687bd228b8eba8917f46bcbbe1a9289c00cd6403`](https://explorer-studio.genlayer.com/tx/0x0ff90143ff9db110876cdbb4687bd228b8eba8917f46bcbbe1a9289c00cd6403), **FINALIZED, Result: ERROR**): the same `wikipedia.org` target with 2 of 3 evidence URLs on Wikipedia's own domain. Every validator independently rejected the call with the identical rollback message before any fetch happened: `"At least 2 of the submitted evidence_urls must resolve to distinct, non-self-reported, non-denylisted domains (found 1)"`.

**Transaction 3 — self-reported evidence excluded despite a positive verdict** (tx [`0x09ebd394fea6db1e61997d480cafd0092595c678a041fd8371be9031465b8d96`](https://explorer-studio.genlayer.com/tx/0x09ebd394fea6db1e61997d480cafd0092595c678a041fd8371be9031465b8d96), **FINALIZED**): `submit_check("wikipedia.org", ["https://en.wikipedia.org/wiki/Wikipedia", "https://www.britannica.com/topic/Wikipedia", "https://www.reuters.com/technology/"])`. Result (`check_id "1"`): the Wikipedia article — hosted on the target's own domain — was fetched successfully and judged `IndicatesLegitimate`, and correctly flagged `is_self_reported: true`. Despite this favorable verdict, it was excluded from corroboration (`independent_domain_count: 0`). The two genuinely third-party sources both failed to fetch (`inaccessible`). `final_verdict: "InsufficientEvidence"` — exactly the intended behavior: a self-published favorable page cannot single-handedly produce a positive verdict, even when the only other candidates happen to fail.

**Transaction 4 — self-report AND duplicate-domain stacking, via a subdomain** (tx [`0x9384eca2797214817c003105f616af8c01b1411bd4388e0923d6874eaa04b578`](https://explorer-studio.genlayer.com/tx/0x9384eca2797214817c003105f616af8c01b1411bd4388e0923d6874eaa04b578), **FINALIZED**): `submit_check("wikipedia.org", ["https://en.wikipedia.org/wiki/Wikipedia", "https://simple.wikipedia.org/wiki/Wikipedia", "https://www.britannica.com/topic/Wikipedia", "https://www.investopedia.com/terms/w/wikipedia.asp"])`. Result (`check_id "2"`): `en.wikipedia.org` was fetched, judged `IndicatesLegitimate`, and flagged `is_self_reported: true`. `simple.wikipedia.org` — a *different* Wikipedia subdomain — reduced to the exact same registrable domain (`wikipedia.org`) and was correctly flagged **both** `is_duplicate_domain: true` **and** `is_self_reported: true` simultaneously, live confirmation that subdomain-independence and self-report detection use the same underlying domain reduction and stack correctly. Both `britannica.com` and `investopedia.com` failed to fetch (`inaccessible`). With zero eligible domains, `final_verdict: "InsufficientEvidence"` (`self_reported_count: 2`, `duplicate_domain_count: 1`).

**Consensus note (all transactions):** every transaction reached `ACCEPTED` → `FINALIZED` via `gl.eq_principle.prompt_comparative`, not exact string matching. `Idle` / "Validator execution cancelled after quorum" entries are GenVM's own optimization once enough validators agree, not faults.

## Design Rationale: The Self-Vouching Problem

A domain under suspicion of being a scam has every incentive to make itself look legitimate — and unlike a neutral fact-checking claim (where nobody obviously benefits from a false "Verified" result), scam verification is adversarial by nature: the entity being evaluated actively wants a favorable outcome and controls content on its own domain.

Three deterministic, structural design choices address this — deliberately *not* delegated to LLM judgment, since a sufficiently motivated actor can word their way past a purely content-based check:

1. **`is_self_reported` exclusion** (the headline mechanic): any evidence URL whose registrable domain matches the target's registrable domain — including any subdomain — is fetched and judged like any other source (nothing is hidden), but is categorically excluded from corroboration in `_aggregate`. See `_annotate_evidence` / `_aggregate` in `contract.py`.
2. **Pre-flight rejection of all-self-reported submissions**: if every submitted evidence URL turns out to be on the target's own domain, `submit_check` rejects the call *before* spending any fetch/LLM cost, rather than quietly resolving to `InsufficientEvidence` after paying for it.
3. **Multiple independent domains required, always**: exactly the same `MIN_INDEPENDENT_DOMAINS`-style requirement used by comparable corroboration contracts (see the companion TruthBeacon fact-checking contract, which pioneered this pattern for a different problem — duplicate/Sybil domains rather than self-vouching) — a single source, self-reported or not, can never be sufficient.

Full threat-model detail and what this does *not* protect against (e.g. a genuinely independent third-party site that happens to be complicit): [SECURITY.md § 1](SECURITY.md#1-self-vouching--fake-independent-corroboration).

## Architecture (Summary)

```
submit_check(target_domain, evidence_urls)
        │
        ├─ 1. Deterministic input validation (cheap, fails fast, no gl.* calls)
        │      target_domain normalized & validated
        │      3 ≤ len(evidence_urls) ≤ 6
        │      ≥ 2 distinct, non-self-reported, non-denylisted domains
        │
        ├─ 2. Deterministic provenance annotation (_annotate_evidence)
        │      registrable domain per URL · duplicate flag · denylist flag
        │      is_self_reported flag against target_domain
        │
        ├─ 3. ONE non-deterministic closure (gl.eq_principle.prompt_comparative)
        │      per evidence URL: fetch → classify → LLM judge →
        │      fixed-vocabulary verdict → deterministic aggregation
        │      (gated on duplicate/denylist/self-reported) → one final
        │      verdict + stats
        │
        └─ 4. Persist target domain + verdict + full evidence trail to
              on-chain storage
```

Full component diagrams, sequence diagrams, and the "why `prompt_comparative` not `strict_eq`" rationale: [ARCHITECTURE.md](ARCHITECTURE.md).

## Aggregation Logic

`_aggregate` only considers **eligible** records: `fetch_status == "ok"`, not a duplicate domain, not low-credibility, and **not self-reported**. Let `scam`/`legit` be the count of eligible `IndicatesScam`/`IndicatesLegitimate` verdicts, and `independent_total` be the total count of distinct eligible domains.

| Final verdict | Exact condition |
|---|---|
| **InsufficientEvidence** | `independent_total < 2` — not enough independent, credible, third-party, reachable evidence to say anything |
| **LikelyScam** | `scam >= 2` **and** `scam > legit` |
| **LikelyLegitimate** | `legit >= 2` **and** `legit > scam` |
| **Disputed** | Neither above, but `scam > 0` **and** `legit > 0` (a tie or near-tie) |
| **Unverified** | Everything else — enough evidence exists but it's inconclusive |

**Tested nuance:** self-reported evidence is excluded from `independent_total` *categorically*, regardless of its own verdict — a self-published page that (unusually) admits "this is a scam" is still excluded, because the exclusion is about independence, not content (`test_self_reported_excluded_regardless_of_its_own_verdict` in `tests/test_aggregation.py`). Full rationale in [DESIGN_DECISIONS.md § 1](DESIGN_DECISIONS.md#1-why-self-reported-exclusion-is-structural-not-llm-judged).

## Public Interface

```python
submit_check(target_domain: str, evidence_urls: list[str]) -> str   # returns check_id
get_check(check_id: str) -> str      # full JSON evidence record
get_verdict(check_id: str) -> str    # just the final verdict word
total_checks() -> int
```

Example `get_check` result:

```json
{
  "check_id": "0",
  "target_domain": "scam-site.example",
  "final_verdict": "LikelyScam",
  "total_evidence_submitted": 3,
  "independent_domain_count": 2,
  "duplicate_domain_count": 0,
  "failed_source_count": 0,
  "self_reported_count": 1,
  "evidence": [
    {
      "url": "https://scam-site.example/we-are-legit",
      "domain": "scam-site.example",
      "is_duplicate_domain": false,
      "is_low_credibility": false,
      "is_self_reported": true,
      "fetch_status": "ok",
      "verdict": "IndicatesLegitimate"
    },
    {
      "url": "https://reviews.example/scam-site-review",
      "domain": "reviews.example",
      "is_duplicate_domain": false,
      "is_low_credibility": false,
      "is_self_reported": false,
      "fetch_status": "ok",
      "verdict": "IndicatesScam"
    }
  ]
}
```

Note that the self-reported evidence is still present in full, with its actual verdict (`IndicatesLegitimate`) — it isn't hidden or omitted, just excluded from the corroboration count via `is_self_reported: true`. `domain` is the approximate **registrable** domain (see [DESIGN_DECISIONS.md § 3](DESIGN_DECISIONS.md#3-why-an-approximate-registrable-domain-not-a-full-public-suffix-list)), not necessarily the exact fetched hostname — the exact URL is always available in the `url` field.

## Security & Threat Model (Summary)

Self-vouching (the primary threat this contract exists to address), prompt injection (both via fetched evidence content and via the `target_domain` string itself), Sybil-style duplicate-domain stuffing, known-unreliable evidence domains, and fetch failures are all explicitly mitigated with tests. Full threat model, evidence, and residual risks: [SECURITY.md](SECURITY.md).

## Known Limitations (Summary)

No full Public Suffix List, no cross-domain content-similarity detection (a scam operator's *second*, formally-unrelated domain publishing fake positive reviews is not caught by the self-report check), a static (not governance-managed) low-credibility denylist, no spam/staking defense, and consensus reliability that inherently scales with evidence count. Every limitation is disclosed with its specific trade-off reasoning, not hidden: [SECURITY.md § 6](SECURITY.md#6-known-limitations-not-fixed-by-design) and [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md). What a future version could do about each: [ROADMAP.md](ROADMAP.md).

## Testing (Summary)

**128/128 offline tests passing**, organized into 8 files by function under test:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

| File | Tests | Covers |
|---|---|---|
| `test_domain_extraction.py` | 33 | Registrable-domain extraction, subdomains, IPv6, trailing dots, target-domain normalization |
| `test_content_classification.py` | 13 | Malformed/empty/ok content detection |
| `test_aggregation.py` | 17 | Final-verdict decision rule, incl. self-reported/duplicate/low-credibility exclusion |
| `test_parser.py` | 13 | Raw LLM response → fixed vocabulary |
| `test_prompt_and_consensus.py` | 15 | Prompt guardrails, equivalence principle |
| `test_input_validation.py` | 11 | Pre-fetch validation, `gl.vm.UserError` |
| `test_end_to_end.py` | 17 | Full pipeline, adversarial scenarios, self-reported evidence end-to-end |
| `test_storage.py` | 9 | On-chain persistence, multi-check isolation |

Plus an unexecuted `gltest` integration example (`tests/gltest_integration_example.py` — explicitly marked as not-yet-validated). Full three-tier explanation: [TESTING.md](TESTING.md).

## Deploying

Single-file deployment, same as any GenLayer Intelligent Contract — deploy `contract.py` via the GenLayer Studio "Create New Contract" UI (paste or upload the file; the constructor takes no arguments).

This exact contract is already deployed and live — see [Live Deployment](#live-deployment) above.

To exercise it yourself:
- **Write Methods → `submit_check`**: provide `target_domain` (string, e.g. `"scam-site.example"` or a full URL) and `evidence_urls` (JSON array of 3–6 URL strings)
- **Read Methods → `get_check`**: provide the returned `check_id` to see the full evidence record

## Repository Structure

```
scamsiteguard/
├── contract.py                   # the Intelligent Contract (single deployable file)
├── README.md                     # this file
├── ARCHITECTURE.md
├── SECURITY.md
├── DESIGN_DECISIONS.md
├── TESTING.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── ROADMAP.md
├── REVIEWER_GUIDE.md
├── PROJECT_OVERVIEW.md
├── SUBMISSION_CHECKLIST.md
└── tests/
    ├── README.md                 # test coverage index
    ├── _bootstrap.py             # shared offline-stub wiring
    ├── genlayer_stub/            # minimal offline genlayer SDK stub
    ├── test_domain_extraction.py
    ├── test_content_classification.py
    ├── test_aggregation.py
    ├── test_parser.py
    ├── test_prompt_and_consensus.py
    ├── test_input_validation.py
    ├── test_end_to_end.py
    ├── test_storage.py
    └── gltest_integration_example.py   # unexecuted, see TESTING.md
```
