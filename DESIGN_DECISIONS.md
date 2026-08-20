# Design Decisions

Every non-obvious design choice in `contract.py`, with the problem it solves, the alternative(s) considered, and the trade-off accepted.

---

## 1. Why Self-Reported Exclusion Is Structural, Not LLM-Judged

**Problem:** Scam verification is adversarial in a way general fact-checking isn't — the target domain has a direct, obvious incentive to make itself look legitimate, and controls content on its own domain completely. A naive design ("ask the LLM if this evidence looks self-promotional") could be talked past by sufficiently confident, well-written self-published text.

**Chosen solution:** `is_self_reported`, computed deterministically in `_annotate_evidence` by comparing an evidence URL's registrable domain against the target's normalized registrable domain — pure string comparison, zero LLM involvement. `_aggregate` excludes any such record from corroboration unconditionally, regardless of its own verdict.

**Alternative considered:** Add a prompt instruction like "flag if this content appears to be published by the site being evaluated itself." Rejected: the LLM has no reliable way to determine *who actually operates* a domain from page content alone — a well-disguised page (no "About Us" self-identification, professional tone, no obvious tells) could pass right through a content-only check, defeating the entire purpose of the mechanism. A domain-identity fact should be checked as a domain-identity fact, not inferred from writing style.

**Trade-off:** This only catches evidence hosted on the target's own domain (including subdomains) — a *formally distinct* second domain the same operator also controls is not caught (see [SECURITY.md § 8](SECURITY.md#8-formally-unrelated-second-domain-residual-risk)). This is a deliberate, disclosed scope boundary: catching that would require off-chain ownership data with its own trust/determinism problems, or an unreliable content-similarity heuristic — both worse trade-offs than leaving this specific gap open and documented.

---

## 2. Why `TreeMap` for Storage

**Problem:** GenLayer contracts need persistent, chain-backed storage for an unbounded, growing number of checks, addressable by ID.

**Chosen solution:** `check_records: TreeMap[str, str]`, keyed by a monotonically-incrementing string ID (`check_count`, converted to a string).

**Alternative considered:** A `DynArray` of records. Rejected: `TreeMap` gives O(log n) lookup by ID without needing to scan, and string keys avoid any type-coercion ambiguity between the public interface (which takes `check_id: str`) and internal storage.

**Trade-off:** No native enumeration/listing of all check IDs is exposed (a caller must already know or be told a `check_id`, typically the return value of their own `submit_check` call, or discover the range via `total_checks()`). Acceptable for this contract's use case — checks are typically looked up by an ID the caller already has.

---

## 3. Why JSON Storage (One Blob Per Check) Instead of Multiple Fields

**Problem:** A check's full evidence trail is a variable-length list of records, each with several fields — not a natural fit for GenLayer's flat, typed persistent-storage fields.

**Chosen solution:** Serialize the entire record (target domain, final verdict, stats, and the full per-evidence-URL array) as one JSON string per check, stored in the `TreeMap`.

**Alternative considered:** Separate `TreeMap`s per field (e.g. one for verdicts, one for domain lists). Rejected: this would require juggling several storage structures in lockstep, keyed by the same check ID, and would still hit GenLayer's restriction against natively storing nested lists/dicts for the variable-length evidence array — the JSON-blob approach solves that restriction directly rather than working around it repeatedly.

**Trade-off:** Any read of a single field (e.g. just the final verdict) requires deserializing the whole blob — mitigated by providing `get_verdict` as a dedicated convenience accessor for the common case.

---

## 4. Why `prompt_comparative`, Not `strict_eq`

**Problem:** LLM calls across independent validators are not guaranteed to produce byte-identical output even when they reach the same substantive conclusion.

**Chosen solution:** `gl.eq_principle.prompt_comparative(nondet, principle=EQUIVALENCE_PRINCIPLE)` — GenLayer's documented mechanism for LLM-derived, non-byte-identical consensus.

**Alternative considered:** `gl.eq_principle.strict_eq()`. Rejected outright — GenLayer's own guidance is explicit that `strict_eq` must never be used for LLM-derived output; using it here would risk spurious consensus failures unrelated to whether the actual verdict was correct.

**Trade-off:** None significant — this is the SDK-correct choice for this workload, not a compromise.

---

## 5. Why Bounded Evidence Count (3–6)

**Problem:** Too few sources (1) can't establish independent corroboration at all; unbounded sources let a caller force unlimited fetch/LLM cost per call.

**Chosen solution:** `MIN_EVIDENCE_SUBMITTED = 3`, `MAX_EVIDENCE_SUBMITTED = 6`.

**Alternative considered:** No upper bound, relying on gas/execution cost alone to discourage abuse. Rejected: an explicit, cheap, pre-flight bound fails fast and predictably, rather than relying on cost economics that could vary across deployments.

**Trade-off:** A genuinely well-evidenced check with more than 6 credible sources can't submit all of them in one call — acceptable, since `MIN_INDEPENDENT_DOMAINS = 2` is already the threshold that actually matters for a verdict, and 6 is generous headroom above that.

---

## 6. Why Fixed Vocabularies

**Problem:** `prompt_comparative`'s NLP comparator needs a simple, well-defined equivalence check, not open-ended prose comparison.

**Chosen solution:** Every LLM-influenced or aggregation-derived output value is restricted to a small, hardcoded tuple of exact strings (`EVIDENCE_VERDICTS`, `FETCH_STATUSES`, `FINAL_VERDICTS`) — `_parse_evidence_verdict` and `_aggregate` never return anything outside these sets.

**Alternative considered:** Free-form LLM explanation text, judged for "equivalent meaning" by the comparator. Rejected: this makes the comparator's job much harder and less predictable, and provides no benefit — the contract only ever needs to *act* on a categorical verdict, not display prose.

**Trade-off:** No nuance or explanation is captured in the stored verdict beyond the category itself — acceptable, since the full evidence URL and raw fetch status are still persisted for a human reviewer to investigate further if desired.

---

## 7. Why Conservative Aggregation

**Problem:** A single agreeing source, or a narrow majority among unreliable evidence, shouldn't be enough to brand a domain as a scam (with real reputational consequences) or clear it as legitimate (with real fraud-risk consequences).

**Chosen solution:** `MIN_INDEPENDENT_DOMAINS = 2` minimum eligible domains before any directional verdict; `LikelyScam`/`LikelyLegitimate` additionally require a strict majority (`count > other_count`), not merely `count >= 2`.

**Alternative considered:** A simple majority-of-all-submitted-evidence rule with no independence floor. Rejected: this would let 2 duplicate-domain or self-reported sources plus 1 real one produce a false sense of "3 sources agree."

**Trade-off:** A tied 1-vs-1 result (or a 2-vs-2 result) resolves to `Disputed` rather than picking a side — intentional; see [README.md § Aggregation Logic](README.md#aggregation-logic).

---

## 8. Why Deterministic Preprocessing (Before Any Non-Deterministic Step)

**Problem:** Input validation, domain extraction, and self-report detection don't need network access or an LLM — running them inside the `nondet()` closure anyway would mean redundant work per validator and would make bugs harder to unit-test in isolation.

**Chosen solution:** All of `_normalize_target_domain`, `_annotate_evidence`, `_extract_domain`, and `_registrable_domain` run BEFORE `submit_check` ever constructs the `nondet()` closure — pure functions of caller-supplied strings, safe to call directly in offline tests with zero mocking.

**Trade-off:** None significant — this is a strict improvement in both cost and clarity, since deterministic logic is also the easiest to unit-test exhaustively (72 of the 128 offline tests exercise pure deterministic functions with zero mocking required — see [tests/README.md](tests/README.md)).

---

## 9. Why an Approximate Registrable Domain, Not a Full Public Suffix List

**Problem:** Comparing "is this evidence URL on the target's own domain" (and "are two evidence URLs on the same domain") correctly requires knowing where a public suffix ends and a registrable name begins (e.g. `co.uk` isn't itself a registrable domain, but `bbc.co.uk` is) — a full, precise answer requires the actual Public Suffix List, an external, frequently-updated data source.

**Chosen solution:** `KNOWN_MULTI_PART_SUFFIXES`, a small, hardcoded, auditable set of the most common two-label suffixes (`co.uk`, `com.au`, ...) under which three labels are kept instead of two.

**Alternative considered:** Fetch a live PSL at runtime. Rejected outright — this would require network access from inside consensus-critical, deterministic code, and could return different data to different validators at different times, breaking the determinism GenVM contracts require.

**Trade-off:** Rare multi-part suffixes not in the hardcoded list will be handled incorrectly (treated as a shared domain when they shouldn't be, or vice versa) — a documented, disclosed limitation, not a silent one (see [SECURITY.md § 10](SECURITY.md#10-known-limitations-not-fixed-by-design)).

---

## 10. Why a Static Denylist Instead of a Reputation Score

**Problem:** Some domains are known, low-value sources of unreliable content (satire sites, content farms) — should evidence from them count toward corroboration at all?

**Chosen solution:** `LOW_CREDIBILITY_DOMAINS`, a small, fixed, hardcoded denylist, checked deterministically. Evidence from these domains is still fetched and recorded (transparency), but excluded from corroboration.

**Alternative considered:** A numeric, continuously-updated reputation score per domain. Rejected for this initial version: a live, mutable reputation feed has the same determinism problem as a live PSL fetch — it would need to be either a governance-controlled on-chain registry (a larger, separate feature) or an off-chain oracle (introducing its own trust assumptions). A small, auditable, contract-code-embedded denylist is deterministic by construction and transparent to any reviewer reading the source.

**Trade-off:** The list is small, illustrative, and requires a contract upgrade to extend — acceptable for an initial submission, explicitly flagged as a production gap. See [ROADMAP.md](ROADMAP.md) for the governance-registry alternative.
