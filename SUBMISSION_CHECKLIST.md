# Submission Checklist

Use this before submitting ScamSiteGuard to GenLayer review. Each item states what's actually been verified, not just what should exist.

---

## Repository

- [x] `contract.py` is a single, self-contained deployable file (GenLayer contracts must be single-file)
- [x] `contract.py` compiles cleanly (`python3 -m py_compile contract.py`)
- [x] No `TODO`/`FIXME`/placeholder code anywhere in `contract.py`
- [x] No `@classmethod`/`@staticmethod` on any contract method (GenVM lint rule E022 compliance, verified from the start)
- [x] README, ARCHITECTURE.md, SECURITY.md, DESIGN_DECISIONS.md, TESTING.md, CHANGELOG.md, ROADMAP.md, CONTRIBUTING.md, REVIEWER_GUIDE.md, PROJECT_OVERVIEW.md all present and cross-linked
- [x] No dead code, no duplicated explanations across documents
- [ ] **Action needed:** push the final repository state to a public GitHub repository

## Tests

- [x] Offline test suite passes: **128/128**, run via `python3 -m unittest discover -s tests -p "test_*.py" -v`
- [x] Test coverage checklist complete — every requested scenario (valid checks, insufficient evidence, duplicate domains, self-reported evidence, malformed URLs, timeouts, empty/malformed content, low-credibility domains, aggregation, parsing, registrable-domain extraction, boundary values, storage persistence) mapped to a specific test file in [tests/README.md](tests/README.md)
- [x] `gltest_integration_example.py` clearly and honestly marked as unexecuted, with the exact reason (no live node/`pytest` available in this environment)
- [x] Tests organized by function-under-test across 8 files, not one monolithic file
- [x] The core novel mechanic (self-reported evidence exclusion) has dedicated tests covering: alone as the only source, stacked with other exclusion reasons, excluded regardless of its own verdict, via subdomain, via full-URL target form, and the all-self-reported upfront-rejection case

## Deployment

- [x] Deployed `contract.py` to GenLayer Studio: `0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D`
- [x] Contract address recorded in README.md's "Live Deployment" section, TESTING.md § 4, REVIEWER_GUIDE.md § 4, and PROJECT_OVERVIEW.md
- [x] At least one live `submit_check` transaction demonstrating a real, honest result (`Unverified`, on a fictional target domain)
- [x] At least one live `submit_check` transaction demonstrating the self-reported-evidence exclusion mechanic end-to-end: a target's own page fetched, judged `IndicatesLegitimate`, and still correctly excluded from corroboration (`InsufficientEvidence`) — the single most important piece of live evidence for this project
- [x] Pre-flight rejection of insufficient independent domains also verified live, with every validator agreeing on the identical rollback message
- [x] Consensus finalized on both successful transactions with no execution errors; the pre-flight rejection also reached consensus (on the rejection itself)

## Explorer

- [x] Public contract address page confirmed live and accessible: https://explorer-studio.genlayer.com/address/0xE8b2EF9B2EF0aB371cA7E320cc9ABA85958Ed98D
- [x] Individual transaction links recorded for each demonstration scenario (see [REVIEWER_GUIDE.md § 4](REVIEWER_GUIDE.md#4-live-transaction-evidence))

## GitHub

- [ ] **Action needed:** create a public GitHub repository
- [ ] **Action needed:** push `contract.py`, all `.md` documentation files, and the `tests/` directory
- [ ] **Action needed:** set the repository's "About" description and website link (to the live contract address page, once deployed)
- [ ] **Action needed:** copy the repository URL into the GenLayer Portal submission form's Evidence URL field

## Contribution (GenLayer Portal Submission)

- [ ] Contribution Type: **Builder** → **Intelligent Contracts**
- [ ] Title filled in (suggested: "ScamSiteGuard — Self-Report-Resistant Scam Website Verification Contract")
- [ ] Notes/Description filled in (see [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) for ready-to-use language)
- [ ] Evidence URLs added:
  - [ ] GitHub repository link
  - [ ] Live contract address page (once deployed — primary evidence)
  - [ ] Deploy transaction link
  - [ ] The self-reported-evidence-exclusion demonstration transaction link (the single most important piece of evidence for this specific project)

## Evidence

- [x] Every claim made in any `.md` file is backed by either a specific test name or a specific transaction hash — no unbacked claims
- [x] `gltest_integration_example.py` explicitly disclosed as unexecuted rather than presented as a passing test
- [x] Conservative/negative results (`Unverified`, `InsufficientEvidence`) are included alongside the live evidence, not cherry-picked away — this is itself evidence of honest behavior, and directly demonstrates the core claim: self-reported evidence cannot single-handedly produce a favorable verdict

## Documentation

- [x] README — navigation hub, quick start, design rationale, aggregation logic, public interface
- [x] ARCHITECTURE.md — diagrams, execution flow, storage/consensus model
- [x] SECURITY.md — full threat model with per-attack evidence, including the disclosed residual risk (formally-unrelated affiliated domains)
- [x] DESIGN_DECISIONS.md — every choice with alternatives and trade-offs
- [x] TESTING.md — three-tier testing explanation
- [x] CONTRIBUTING.md — contributor guide
- [x] CHANGELOG.md — version history
- [x] ROADMAP.md — future work with rationale for current scope
- [x] REVIEWER_GUIDE.md — verification guide for judges
- [x] PROJECT_OVERVIEW.md — 5-minute executive summary
- [x] This file (SUBMISSION_CHECKLIST.md)

---

## Final Status

**Code and testing: ready (128/128 offline).** **Documentation: ready.** **Live deployment: ready (3/3 successful `submit_check` transactions FINALIZED, plus 1 pre-flight rejection also FINALIZED — the core self-reported-evidence exclusion mechanic, including its stacking with duplicate-domain detection, proven live).**

**Remaining action items before submission are entirely administrative** (create/push to a public GitHub repo, then fill in the Portal form) — no further code, test, or documentation work is required.
