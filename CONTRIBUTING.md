# Contributing to ScamSiteGuard

Thanks for your interest in improving ScamSiteGuard. This is an educational reference implementation of a GenLayer Intelligent Contract, and contributions that improve correctness, clarity, test coverage, or documentation accuracy are welcome.

## Before You Start

Read these first, in order:
1. [ARCHITECTURE.md](ARCHITECTURE.md) — how the contract is structured and why
2. [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) — why specific choices were made, and what alternatives were rejected
3. [SECURITY.md](SECURITY.md) — the threat model, so you understand what a change might weaken
4. [tests/README.md](tests/README.md) — how the test suite is organized

## Ground Rules

- **`is_self_reported` exclusion is the core mechanic — treat it as load-bearing.** It's deliberately a deterministic domain-match check, not an LLM judgment call. Do not "simplify" this into a prompt instruction without reading [DESIGN_DECISIONS.md § 1](DESIGN_DECISIONS.md#1-why-self-reported-exclusion-is-structural-not-llm-judged) first — that's exactly the design that was considered and rejected.
- **This contract's consensus mechanism is deliberate, not accidental.** It uses `gl.eq_principle.prompt_comparative`, not `strict_eq`, specifically because GenLayer's documentation states `strict_eq` must never be used for LLM-derived output. See [DESIGN_DECISIONS.md § 4](DESIGN_DECISIONS.md#4-why-prompt_comparative-not-strict_eq).
- **Never widen the fixed vocabularies casually.** `EVIDENCE_VERDICTS`, `FETCH_STATUSES`, and `FINAL_VERDICTS` are small and closed specifically so the consensus comparator's job stays well-defined. Adding a new value requires updating `EQUIVALENCE_PRINCIPLE`, `_aggregate`, and the relevant tests together, not in isolation.
- **Never remove test coverage.** If you refactor a test file, every scenario it covered must still be covered afterward — extend or reorganize, don't delete.
- **Keep the non-deterministic closure's return value fixed-vocabulary-only.** Never add raw fetched content, timestamps, or exact byte counts to what `nondet()` returns — this is what keeps consensus reliable. See [SECURITY.md § 9](SECURITY.md#9-consensus-assumptions).
- **`_aggregate` reads `is_self_reported` via direct indexing, not `.get()`.** Unlike an optional add-on flag, it's a required field this contract always produces — a record missing it should raise loudly, not silently default to "eligible." Don't change this without understanding why (see the comment in `_aggregate`'s docstring).

## Development Workflow

1. **Run the full test suite before and after your change:**
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py" -v
   ```
   All 128 tests must pass. If your change is a bug fix, add a test that fails before your fix and passes after.

2. **Compile-check the contract:**
   ```bash
   python3 -m py_compile contract.py
   ```

3. **If you change any `gl.*` API call**, verify it against GenLayer's current SDK documentation before submitting.

4. **If you change a threshold or constant** (e.g. `MIN_EVIDENCE_SUBMITTED`, `MIN_INDEPENDENT_DOMAINS`), update:
   - The relevant docstring/comment in `contract.py`
   - Any README table or example that references the old value
   - Any test that hardcodes boundary values around it

## What Kinds of Contributions Are Welcome

- **Bug fixes** with a regression test.
- **New test coverage** for scenarios not yet exercised (check `tests/README.md`'s coverage checklist first).
- **Documentation corrections** — if you find a claim in any `.md` file that doesn't match the actual code or test behavior, that's a real bug in this repository and a very welcome PR.
- **SDK compatibility fixes** if GenLayer's SDK changes underneath this contract.
- **Progress on [ROADMAP.md](ROADMAP.md) items**, especially the affiliated-domain exclusion list (§1), which is the most-requested extension to the core anti-self-vouching mechanic.

## What This Project Deliberately Does NOT Want

- Architectural rewrites without a demonstrated bug — see [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) for why the current structure was chosen.
- New "smart" features (cross-domain content similarity, reputation scoring, staking) added directly to `contract.py` — these are real, valuable ideas, but belong in [ROADMAP.md](ROADMAP.md) discussion first, since each has real determinism/consensus trade-offs that need to be worked out before code.
- Removing disclosed limitations from the README instead of fixing them — if a limitation in [SECURITY.md](SECURITY.md) or [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) bothers you, propose a fix, don't just delete the disclosure.
- Replacing `is_self_reported`'s deterministic domain check with an LLM-based heuristic "for flexibility" — this defeats the entire point of the mechanism (see Ground Rules above).

## Reporting Issues

When reporting a bug, please include:
- Whether it's in the deterministic pre-flight logic, the non-deterministic evaluation logic, or the documentation
- A minimal `target_domain` + `evidence_urls` combination that reproduces it (for contract bugs)
- Which test file, if any, should have caught it but didn't

## Style

- Match the existing comment density in `contract.py` — every non-obvious decision has a "why" comment nearby. New code should too.
- Test files are organized by *what they test*, not by *which review round found them* (see `tests/README.md`). Put new tests in the file matching the function or scenario they cover, not in a new catch-all file.
