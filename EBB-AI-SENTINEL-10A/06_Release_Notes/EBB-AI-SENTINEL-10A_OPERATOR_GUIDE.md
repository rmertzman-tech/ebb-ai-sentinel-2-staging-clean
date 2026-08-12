# EBB-AI-SENTINEL-10A Operator Guide

1. Upload the ordinary `EBB-AI-SENTINEL-10A` folder to the staging repository and commit it to `main`.
2. Separately upload only `sentinel10a-live-certification.yml` to repository root `.github/workflows/` and commit it separately.
3. In Actions, select **EBB AI SENTINEL-10A RC2.7-vs-RC2.8 Production-Compatible Live Certification**.
4. Verify branch `main` and endpoint `https://ucp-backend-4dig.onrender.com/api/claude-proxy`.
5. Launch exactly one run.
6. On success, download the separation receipt first. Do not access the custodian artifact before the strict blind review is locked.
7. Verify separation PASS and 147 blind records.
8. Review only the blind artifact, lock judgments, then obtain the custodian artifact for reconciliation and unblinding.

The independent 12-case paraphrased holdout set is not part of this run.
