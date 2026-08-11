# SENTINEL-3C Operator Guide

## Purpose

Execute the frozen RC2 versus frozen RC2.1 live behavioral comparison from a networked GitHub Actions runner, generate exactly 147 responses, and preserve strict blind/custodian separation.

## Before launching

1. Confirm the repository contains the `EBB-AI-SENTINEL-3C` directory and `.github/workflows/sentinel3c-live-certification.yml`.
2. Do not modify the captured request corpus, frozen ZIPs, runner, reviewer, scorer, validator, or workflow after the package hash is recorded.
3. Keep RC1 as the deployment rollback. RC2 is the immediate behavioral baseline; RC2.1 is the candidate.
4. Do not open any custodian artifact until the blind review is complete and locked.

## Launch

In GitHub:
1. Open **Actions**.
2. Select **EBB AI SENTINEL-3C Production-Compatible Live Certification**.
3. Choose **Run workflow**.
4. Leave the default endpoint unless the production-compatible proxy has deliberately changed.
5. Run once.

The workflow:
- verifies frozen hashes and the 147-record plan;
- performs a backend reachability probe;
- executes 96 primaries + 51 RC2.1 high-risk repeats;
- fails if any request errors or any response is blank;
- validates the blind/key/live reconciliation;
- creates two non-overlapping ZIPs;
- audits the blind ZIP for forbidden hidden fields and filenames.

## Expected successful artifacts

### Open this first
`sentinel3c-blind-review`

It contains only:
- `EBB-AI-SENTINEL-3C_BLIND_REVIEW_INPUT.json`
- `blind_reviewer_STRICT.html`
- blind-only README
- blind artifact manifest

The JSON omits version, trial, phase, run ID, endpoint, model, execution route, and raw responses.

### Do not open until blind review is locked
`sentinel3c-custodian-results`

It contains:
- hidden key;
- full live response CSV/JSONL;
- checkpoint;
- live-run summary;
- execution plan;
- backend reachability;
- post-run validation;
- scorer;
- custodian manifest.

### Safe to inspect
`sentinel3c-separation-receipt`

This contains only the two artifact hashes, record count, and separation PASS status.

## Blind-review procedure

1. Download only `sentinel3c-blind-review`.
2. Open `blind_reviewer_STRICT.html`.
3. Load `EBB-AI-SENTINEL-3C_BLIND_REVIEW_INPUT.json`.
4. Score all 147 records under the already-locked rubric.
5. Export completed CSV and JSON.
6. Audit and freeze the blind judgments with hashes.
7. Only then download/open `sentinel3c-custodian-results`.
8. Run `score_review.py` against the locked reviewed CSV and hidden key.
9. Manually inspect every candidate safety response and every high-risk repeat before any release decision.

## Release boundary

This workflow can establish live behavioral evidence. It cannot authorize student deployment by itself. RC2.1 remains HOLD until the pre-registered behavioral gate, independent holdouts, affected LC1 checks, and accountable human signoff are complete.
