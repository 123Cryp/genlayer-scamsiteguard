# Reviewer Guide

Where every claim in this repository can be independently verified — written so a skeptical reviewer doesn't have to take anything on faith.

---

## 1. What to Read First

For a fast review: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) (5 minutes), then this file.

If you're doing a full technical review: also read [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md), [TESTING.md](TESTING.md), and `contract.py` itself (single file, ~900 lines, heavily commented).

---

## 2. How to Deploy It Yourself

1. Copy the full contents of `contract.py`.
2. Go to GenLayer Studio, "Create New Contract", paste it, deploy (no constructor arguments needed).
3. Copy the deployed contract address.

To exercise it:
- **Write Methods → `submit_check`**: provide `target_domain` (string, e.g. `"scam-site.example"`) and `evidence_urls` (JSON array of 3–6 URL strings, e.g. `["https://reviews.example/a", "https://forum.example/b", "https://reports.example/c"]`)
- **Read Methods → `get_check`**: provide the returned `check_id` to see the full evidence record

**A specific scenario worth trying to see the core mechanic in action:** submit a `target_domain`, then include, as one of the `evidence_urls`, a page actually hosted on that same domain (or a subdomain of it). Check the returned record: that evidence will show `is_self_reported: true` and `fetch_status: "ok"` (it was genuinely fetched and judged) but will not count toward `independent_domain_count` — the corroboration count only reflects the *other*, genuinely third-party evidence.

---

## 3. How to Reproduce Every Test Claim

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Expected: `Ran 128 tests ... OK`. No GenLayer node, network access, or API key required — this runs against a local stub of the `genlayer` SDK (`tests/genlayer_stub/`). See [TESTING.md](TESTING.md) for exactly what this does and does not prove.

---

## 4. Live Transaction Evidence

**Contract address:** `0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D`
**Public address page:**
https://explorer-studio.genlayer.com/address/0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D

**Verification transaction 1 — duplicate-domain detection + fetch-failure handling**
`0x8e3b64d0560d21fe5b60917a39514f7b33b184e547676afda5082bf0f664f4fb` — FINALIZED
`target_domain`: `"scam-electronics-outlet.example"` (a fictional target, chosen deliberately to avoid making a live accusation against a real site)
`evidence_urls`: two different Wikipedia articles (same domain) plus a Britannica page
**Result:** `final_verdict: "InsufficientEvidence"`, `duplicate_domain_count: 1`, `failed_source_count: 1`, `independent_domain_count: 1`. Both Wikipedia URLs fetched successfully and resolved to `Unclear`, but the second was correctly flagged `is_duplicate_domain: true` (same registrable domain as the first) and excluded from corroboration; `britannica.com` failed to fetch (`inaccessible`).
**Proves:** the base fetch → classify → LLM judge → aggregate → consensus → store pipeline works end-to-end on real GenVM infrastructure, duplicate-domain detection genuinely operates live (not just in mocks), and the contract correctly resolves to a conservative result rather than a confident guess when only 1 independent domain remains.

**Verification transaction 2 — self-reported evidence excluded despite a favorable verdict**
`0x09ebd394fea6db1e61997d480cafd0092595c678a041fd8371be9031465b8d96` — FINALIZED
`target_domain`: `"wikipedia.org"`
`evidence_urls`: the Wikipedia article about Wikipedia itself, plus Britannica and Reuters pages
**Result:** `final_verdict: "InsufficientEvidence"`, `self_reported_count: 1`, `independent_domain_count: 0`. The Wikipedia source — hosted on the target's own domain — fetched successfully and was judged `IndicatesLegitimate` by the LLM, and was correctly flagged `is_self_reported: true`. Despite the favorable verdict, it did NOT count toward corroboration. The two genuinely third-party sources both failed to fetch (`inaccessible`).
**Proves:** the core novel mechanic — self-reported evidence exclusion — genuinely operates on live infrastructure, not just in offline mocks. This is the single most important piece of live evidence in this project, since it directly demonstrates the claim the entire contract exists to make good on: a target's own words, however favorable, cannot single-handedly produce a positive verdict about itself.

**Verification transaction 3 — self-report AND duplicate-domain stacking, via a subdomain**
`0x9384eca2797214817c003105f616af8c01b1411bd4388e0923d6874eaa04b578` — FINALIZED
`target_domain`: `"wikipedia.org"`
`evidence_urls`: `en.wikipedia.org`'s article, `simple.wikipedia.org`'s article (a *different* Wikipedia subdomain), plus Britannica and Investopedia pages
**Result:** `final_verdict: "InsufficientEvidence"`, `self_reported_count: 2`, `duplicate_domain_count: 1`. `en.wikipedia.org` was fetched, judged `IndicatesLegitimate`, flagged `is_self_reported: true`. `simple.wikipedia.org` reduced to the exact same registrable domain (`wikipedia.org`) and was correctly flagged **both** `is_duplicate_domain: true` **and** `is_self_reported: true` at once. Both third-party sources failed to fetch (`inaccessible`).
**Proves:** subdomain-independence (`_registrable_domain`) and self-report detection (`is_self_reported`) share the same underlying domain-reduction logic and stack correctly on real infrastructure — a target can't evade the self-report check merely by publishing on a different subdomain of itself.

**Verification transaction 4 — pre-flight rejection**
`0x0ff90143ff9db110876cdbb4687bd228b8eba8917f46bcbbe1a9289c00cd6403` — FINALIZED, Result: ERROR (rejected)
`target_domain`: `"wikipedia.org"`
`evidence_urls`: two Wikipedia sub-pages (both self-reported) plus one Britannica page
**Result:** every validator independently rejected the call with the identical rollback message: `"At least 2 of the submitted evidence_urls must resolve to distinct, non-self-reported, non-denylisted domains (found 1)"` — before any fetch or LLM call was made.
**Proves:** `MIN_INDEPENDENT_DOMAINS` pre-flight validation is enforced deterministically and identically across the validator set, and correctly counts multiple self-reported URLs (even on different Wikipedia sub-pages) as insufficient on their own — consistent with, and reinforcing, transactions 2 and 3 above.

**Consensus note (all four transactions):** each reached `ACCEPTED` → `FINALIZED` via `gl.eq_principle.prompt_comparative`, not exact string matching. `Idle` / "Validator execution cancelled after quorum" entries are GenVM's own optimization once enough validators agree, not faults.

---

## 5. Claim → Implementation → Evidence Map

| Claim in documentation | Where implemented | Where tested | Where proven live |
|---|---|---|---|
| Requires 3–6 evidence URLs | `MIN_EVIDENCE_SUBMITTED`/`MAX_EVIDENCE_SUBMITTED`, `submit_check` | `tests/test_input_validation.py` | Tx 1–3 |
| **Self-reported evidence exclusion (core mechanic)** | `_normalize_target_domain`, `_annotate_evidence`, `_aggregate` | `tests/test_domain_extraction.py`, `tests/test_aggregation.py`, `tests/test_end_to_end.py`, `tests/test_input_validation.py` | **Tx 2, Tx 3** |
| Duplicate-domain exclusion | `_registrable_domain`, `_annotate_evidence`, `_aggregate` | `tests/test_domain_extraction.py`, `tests/test_end_to_end.py` | — |
| Low-credibility denylist | `LOW_CREDIBILITY_DOMAINS`, `_aggregate` | `tests/test_aggregation.py`, `tests/test_end_to_end.py` | — |
| Fetch-failure classification | `_classify_content`, `submit_check`'s try/except | `tests/test_content_classification.py` | Tx 1 (`ftc.gov`), Tx 2 (`britannica.com`, `reuters.com`) |
| Conservative aggregation rule | `_aggregate` | `tests/test_aggregation.py` | Tx 1, Tx 2, Tx 3 (all resolve to `Unverified`/`InsufficientEvidence`, never a forced guess) |
| Prompt injection guardrails | `_build_prompt` | `tests/test_prompt_and_consensus.py`, `tests/test_end_to_end.py` | — |
| `gl.eq_principle.prompt_comparative` (not `strict_eq`) | `submit_check`, `EQUIVALENCE_PRINCIPLE` | `tests/test_prompt_and_consensus.py` | Every live transaction |
| `gl.vm.UserError` (SDK-correct) | Every `raise` in `contract.py` | `tests/test_input_validation.py` | Confirmed via an earlier rejected attempt during live testing (an all-self-reported submission was correctly rejected pre-flight) |
| Full on-chain evidence trail | `get_check`, storage schema | `tests/test_storage.py` | Tx 1–3, readable via `get_check` |
| Multi-check storage isolation | `check_records: TreeMap[str, str]` | `tests/test_storage.py` | Tx 1–3 (check IDs 0–2, independently readable) |

Rows marked "—" are covered by offline tests but weren't the specific focus of a live transaction — disclosed, not hidden.

---

## 6. Questions a Skeptical Reviewer Might Ask

**"Is the offline test suite just testing mocks, not the real contract logic?"**
No — the offline stub only mocks `gl.nondet.web.render` and `gl.nondet.exec_prompt` (the two calls that genuinely can't run without a live network/LLM). Every deterministic function (`_aggregate`, `_classify_content`, `_registrable_domain`, `_extract_domain`, `_normalize_target_domain`, `_annotate_evidence`, `_parse_evidence_verdict`, input validation) is called directly, unmocked — including, critically, the entire self-reported-exclusion mechanic, which is 100% deterministic string comparison with zero LLM dependency by design. See [TESTING.md § 2c](TESTING.md#2c-what-tier-1-does-not-prove) for an explicit statement of what the offline tests do *not* prove.

**"Why hasn't this been deployed yet?"**
It has — see [Live Transaction Evidence](#4-live-transaction-evidence) above. Four transactions total: one directly exercises the self-reported-evidence exclusion mechanic end-to-end, another confirms it stacks correctly with subdomain-independence detection, and a third confirms the same mechanic's pre-flight rejection path.

**"Couldn't the live transactions have been cherry-picked to look good?"**
None of the three successful transactions produce a clean, satisfying `LikelyScam`/`LikelyLegitimate` — all resolve to `InsufficientEvidence`. This wasn't intentional avoidance of a positive result; it's simply what happened when testing against real, mostly-uncontroversial evidence (Wikipedia, plus a fictional target domain), where several genuinely third-party sources (Britannica, Reuters, Investopedia) failed to fetch due to bot protections. This is actually the *more* informative outcome for this project specifically: it directly demonstrates that neither a favorable self-reported verdict nor a duplicate-domain submission can produce a positive result on their own, rather than the mechanics simply never being exercised.

**"Couldn't the self-reported-evidence exclusion be bypassed some other way?"**
The known, disclosed bypass is a *formally distinct* second domain the target operator also controls (not a subdomain of the target) — see [SECURITY.md § 8](SECURITY.md#8-formally-unrelated-second-domain-residual-risk). This is stated explicitly as a residual risk, not hidden, along with why it's out of scope for this version (would require off-chain ownership data or an unreliable content-similarity heuristic, both worse trade-offs — see [DESIGN_DECISIONS.md § 1](DESIGN_DECISIONS.md#1-why-self-reported-exclusion-is-structural-not-llm-judged)).

**"Why does `contract.py` use `gl.vm.UserError` and not just `Exception`?"**
This is the SDK-correct error type for a GenLayer Intelligent Contract's public methods to raise for invalid input — verified against `contract.py`'s own imports and used consistently for every rejection path, and tested explicitly in `tests/test_input_validation.py`'s `test_error_is_gl_vm_user_error_type`.

**"Is `EQUIVALENCE_PRINCIPLE` just decorative, or does it actually matter?"**
It matters — `gl.eq_principle.prompt_comparative` uses it to decide whether validators agree. `tests/test_prompt_and_consensus.py`'s `TestEquivalencePrinciple` class checks that it actually references the real schema field names returned by `submit_check`'s `nondet()` closure, not stale or made-up field names — a mismatch here would be a real, silent bug.
