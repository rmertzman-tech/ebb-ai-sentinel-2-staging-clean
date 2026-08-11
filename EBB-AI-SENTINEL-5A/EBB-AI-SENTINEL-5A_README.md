# EBB-AI-SENTINEL-5A — RC2.2-vs-RC2.3 Production-Compatible Execution Lock

This package freezes the executable 147-record paired certification for the exact SENTINEL-4 RC2.2 baseline and SENTINEL-5 RC2.3 candidate.

- 96 paired primaries: 48 baseline + 48 candidate.
- 94 backend requests + 2 fixed Navigator local interruptions.
- 47/47 backend pairs differ only in the `system` instruction; model, max_tokens, messages, routing, and synthetic user messages are unchanged.
- 51 candidate-only high-risk repeats across the same 17 backend groups.
- Strict reviewer byte-identical to SENTINEL-3C/4A.
- Blind/custodian/separation artifacts remain non-overlapping.
- Frozen scorer logic unchanged apart from stage/version labels.
- External safety-completion token is **not supplied** by the test harness; absence exercises the RC2.3 unresolved-safety rule.
- Offline synthetic validation and blind/custodian packaging smoke tests PASS.
- 12 independent paraphrased holdouts remain unspent.

Status: **READY FOR GITHUB LIVE EXECUTION; HOLD FOR STUDENTS.**
