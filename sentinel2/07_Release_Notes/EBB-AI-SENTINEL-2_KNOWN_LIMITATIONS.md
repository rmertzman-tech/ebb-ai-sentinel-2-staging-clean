# EBB-AI-SENTINEL-2 — Known Limitations

1. **No production-compatible live tutor outputs were generated in the build environment.** The configured backend hostname could not be resolved from the container. This is recorded as an environment limitation, not a behavioral PASS or FAIL.
2. **Captured-request parity is not live behavioral certification.** The harness establishes which exact synthetic requests RC1 and RC2 would send and whether local-versus-backend routing changed. It does not establish how the production model will answer.
3. **Language-model outputs are nondeterministic.** The full certification therefore repeats selected high-risk RC2 cases. Passing one response does not establish universal behavior.
4. **The direct Navigator P06-A safety interruption is narrow.** Its local route is deterministic for the declared trigger case, but this does not prove detection of every possible crisis expression or zero false positives.
5. **Prompt hierarchy does not guarantee model obedience.** All captured RC2 backend system prompts contain the declared safety override, finite-map rule, and symmetric non-manufacturing rule. Live response review remains necessary.
6. **Human review is part of the release evidence.** The blind rubric intentionally tests failures that keyword checks may miss, including softened safety behavior, analysis that continues after depletion, preservation bias, manufactured hidden harm, model reification, and excessive directiveness.
7. **The paired corpus is synthetic.** It tests declared tutor behavior and release risks; it is not a sample of real student mental-health states, institutional conditions, or personal histories.
8. **The patch does not add surveillance or new data collection.** SENTINEL-2 freezes the SENTINEL-1 RC2 source exactly. No new UI, score, classifier, storage field, context expansion, or backend endpoint is introduced.
9. **The package does not claim perfect crisis detection.** Persistent visible human-support access remains primary, and a required safety response is conservative action rather than a diagnosis.
10. **Student promotion remains blocked.** The current authorization is isolated staging only until live paired review and the affected LC1 launch gates pass.
