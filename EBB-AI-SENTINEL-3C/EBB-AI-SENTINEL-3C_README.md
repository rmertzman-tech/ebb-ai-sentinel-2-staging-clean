# EBB-AI-SENTINEL-3C

Production-Compatible RC2-vs-RC2.1 Live Execution, 147-Response Blind Corpus, and Custodian Separation.

## What this build establishes

- The execution target is frozen RC2 versus frozen RC2.1.
- The original 24-scenario / 2-tutor corpus and production-format request pairs are unchanged from SENTINEL-3B.
- Full mode is exactly 147 records: 96 primaries + 51 RC2.1 high-risk repeats.
- A post-run validator fails closed unless all 147 live responses, blind records, hidden-key rows, phases, trials, routes, and response texts reconcile exactly.
- The strict blind JSON structurally omits hidden version/trial/phase and additional custodian metadata.
- Artifact packaging is fail-closed: the blind ZIP is audited for forbidden hidden fields and custodian-like filenames before upload.
- GitHub Actions uploads blind and custodian ZIPs as separate artifacts.
- The scorer reports repeat hard failures, safety-route hard failures, and explicit safety violations separately.

## Current execution status

The current ChatGPT runtime cannot resolve the configured production-compatible backend hostname. No live certification calls were made here. This package is therefore execution-ready rather than falsely labeled as behaviorally complete.

Use `05_Release_Notes/EBB-AI-SENTINEL-3C_OPERATOR_GUIDE.md` to run the workflow from GitHub Actions.
