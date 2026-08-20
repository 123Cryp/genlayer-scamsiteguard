# Roadmap

What's intentionally out of scope for v1.0, and why — each of these is a deliberate boundary, not an oversight (see [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) and [SECURITY.md](SECURITY.md) for the reasoning behind each current limitation).

## Near-term candidates

### 1. Affiliated-domain exclusion list

**Problem it addresses:** [SECURITY.md § 8](SECURITY.md#8-formally-unrelated-second-domain-residual-risk) — a target operator's *formally distinct* second domain (not a subdomain) currently isn't caught by `is_self_reported`.

**Sketch:** an optional `known_affiliated_domains: list[str]` parameter on `submit_check`, analogous in spirit to an allowlist mechanism used by a companion fact-checking contract for a different purpose — but here used as a caller- or governance-declared *denylist* of domains known to be operated by (or affiliated with) the target, excluded from corroboration the same way `is_self_reported` already is. Would need careful design around who is trusted to declare affiliations (self-declared by a concerned third party? Governance-curated? Both, with different weighting?).

### 2. Governance-managed reputation registry

**Problem it addresses:** [DESIGN_DECISIONS.md § 10](DESIGN_DECISIONS.md#10-why-a-static-denylist-instead-of-a-reputation-score) — `LOW_CREDIBILITY_DOMAINS` is currently a small, hardcoded, contract-code-embedded list.

**Sketch:** a separate governance contract that maintains an on-chain, votable registry of low-credibility domains, which this contract reads from instead of (or in addition to) its hardcoded list — keeps the list extensible without a full contract redeployment, while staying deterministic (all validators read the same on-chain state).

### 3. Public Suffix List support

**Problem it addresses:** [DESIGN_DECISIONS.md § 9](DESIGN_DECISIONS.md#9-why-an-approximate-registrable-domain-not-a-full-public-suffix-list) — `KNOWN_MULTI_PART_SUFFIXES` is a small, hand-maintained approximation of the real PSL.

**Sketch:** bundle a periodically-updated, static snapshot of the PSL as contract-embedded data (not a live fetch, to preserve determinism) — a larger but more complete version of the same `KNOWN_MULTI_PART_SUFFIXES` approach already in place.

### 4. Evidence weighting

**Problem it addresses:** currently, all eligible evidence counts equally regardless of source type (a detailed consumer-complaint aggregator page counts the same as a one-line forum post).

**Sketch:** an optional evidence-type classification (news/complaint-board/forum/review-aggregator/other) with different corroboration weight per type — significant added complexity, deferred until the simpler unweighted version has real-world usage to learn from.

### 5. Spam / cost-abuse resistance

**Problem it addresses:** currently, only length/count bounds limit submission cost — no economic disincentive against high-volume low-value submissions.

**Sketch:** a small fee or stake per `submit_check` call, refunded or slashed based on some measure of submission quality — deferred as a separate, larger governance/tokenomics design question outside this contract's core scope.

## Explicitly not planned

- **Off-chain WHOIS/ownership-graph integration**: would require trusting an external, mutable data source inside consensus-critical code — fundamentally in tension with GenVM's determinism requirements, unless done through a separately-designed, properly-decentralized oracle (a much larger undertaking than this contract's scope).
- **Automatic domain blocking/takedown action**: this contract is a verification and evidence-recording tool, not an enforcement mechanism — any downstream action based on its verdicts is intentionally left to the caller/consumer of `get_verdict`, not built into this contract.
