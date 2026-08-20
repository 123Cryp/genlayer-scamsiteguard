# Tests

All tests here run fully offline against a small local stub of the `genlayer` SDK (`genlayer_stub/`) — no GenLayer node, network access, or real LLM required. They import `contract.py` directly and monkeypatch `gl.nondet.web.render` / `gl.nondet.exec_prompt` to simulate specific scenarios deterministically.

## Running

```bash
# everything
python3 -m unittest discover -s tests -p "test_*.py" -v

# a single file
python3 -m unittest tests.test_aggregation -v

# a single test
python3 -m unittest tests.test_aggregation.TestAggregation.test_self_reported_evidence_excluded_even_if_only_source
```

`gltest_integration_example.py` is deliberately excluded from the `test_*.py` discovery pattern (it needs a live GenLayer Studio/node and the `gltest` package) — see its own docstring and the main [README](../README.md) for how to run it separately once you have those available.

## Layout

| File | Tests | What it covers |
|---|---|---|
| `test_domain_extraction.py` | 33 | `_extract_domain` / `_registrable_domain`: subdomain-independence, multi-part suffix handling (`co.uk`, `com.au`, ...), IPv6 literals, trailing DNS dots, length limits, invalid schemes; plus `_normalize_target_domain` for the `target_domain` parameter, including the critical property that a target and its subdomain normalize to the same value |
| `test_content_classification.py` | 13 | `_classify_content`: all five malformed-content checks (length, word count, printable ratio, alpha ratio, diversity) plus boilerplate/captcha detection, and explicit "must NOT false-positive" cases |
| `test_aggregation.py` | 17 | `_aggregate`: every branch of the final-verdict decision rule, including majority-with-dissent, duplicate/low-credibility exclusion, and — the core mechanic — self-reported-evidence exclusion under every combination (alone, stacked with other exclusions, alongside genuine corroboration) |
| `test_parser.py` | 13 | `_parse_evidence_verdict`: exact/case-insensitive matching, multi-line responses, whitespace tolerance, substring false-positive guard |
| `test_prompt_and_consensus.py` | 15 | `_build_prompt` guardrail presence (injection, no-outside-knowledge, skepticism, neutral-mention, insufficient-evidence) and `EQUIVALENCE_PRINCIPLE` schema consistency |
| `test_input_validation.py` | 11 | `submit_check`'s pre-fetch validation: evidence-count bounds, length limits, all-self-reported upfront rejection, `gl.vm.UserError` typing |
| `test_end_to_end.py` | 17 | Full `submit_check` → `get_check` pipeline: clean scam/legitimate verdicts, disputes, duplicates, failures, adversarial sources, prompt injection, and — full end-to-end — self-reported evidence (including via subdomain and full-URL target forms) |
| `test_storage.py` | 9 | `get_check` / `get_verdict` / `total_checks`, and multi-check storage isolation |
| **Total** | **128** | |

## Coverage checklist

- ✅ valid checks (clean scam / clean legitimate) → `test_end_to_end.py`
- ✅ insufficient evidence → `test_input_validation.py`, `test_aggregation.py`, `test_end_to_end.py`
- ✅ duplicate domains → `test_domain_extraction.py`, `test_aggregation.py`, `test_end_to_end.py`
- ✅ self-reported evidence (target vouching for itself), incl. subdomains and stacked exclusions → `test_aggregation.py`, `test_end_to_end.py`, `test_input_validation.py`
- ✅ malformed URLs → `test_domain_extraction.py`
- ✅ timeouts / inaccessible / empty / malformed content → `test_content_classification.py`, `test_end_to_end.py`
- ✅ low-credibility domains → `test_aggregation.py`, `test_end_to_end.py`
- ✅ prompt injection (via evidence content) → `test_prompt_and_consensus.py`, `test_end_to_end.py`
- ✅ aggregation logic → `test_aggregation.py`
- ✅ parser behavior → `test_parser.py`
- ✅ registrable-domain / target-domain normalization → `test_domain_extraction.py`
- ✅ boundary values → length limits and threshold edges across multiple files
- ✅ storage persistence → `test_storage.py`
