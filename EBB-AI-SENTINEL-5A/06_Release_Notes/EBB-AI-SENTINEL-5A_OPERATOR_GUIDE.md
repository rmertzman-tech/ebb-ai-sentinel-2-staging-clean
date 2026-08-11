# EBB-AI-SENTINEL-5A — GitHub Live Execution Operator Guide

## Before launch
1. Keep RC1 rollback, RC2.2 baseline, and RC2.3 candidate frozen.
2. Add the entire `EBB-AI-SENTINEL-5A` directory to the repository without editing its contents.
3. Add `.github/workflows/sentinel5a-live-certification.yml` from the execution-ready package to the repository's exact workflow path.
4. Do not run the 12 independent paraphrased holdouts.
5. Do not open any future custodian artifact until the new 147-record blind review is complete, audited, and cryptographically locked.

## Launch
Actions -> **EBB AI SENTINEL-5A RC2.2-vs-RC2.3 Production-Compatible Live Certification** -> **Run workflow**. Verify `main` and endpoint `https://ucp-backend-4dig.onrender.com/api/claude-proxy`, then launch exactly once.

## Expected execution
The workflow runs fail-closed preflight, then 96 paired primaries + 51 RC2.3 repeats. It validates exact counts, nonblank responses, blind/key reconciliation, strict blind schema, two fixed local P06-A interruptions, 17 repeat groups, and separated artifact packaging.

## On success
Exactly three artifacts should appear:
- `sentinel5a-blind-review` — safe for the blind reviewer.
- `sentinel5a-custodian-results` — **DO NOT OPEN** until the blind review is frozen.
- `sentinel5a-separation-receipt` — safe to inspect first.

Download the separation receipt first, then only the blind artifact. Complete, audit, and hash-lock all 147 blind judgments before obtaining the custodian artifact.

## On failure
Do not rerun immediately. Preserve logs and diagnose the first failing step. Failure diagnostics are custodian material and must not be mixed into a blind review.
