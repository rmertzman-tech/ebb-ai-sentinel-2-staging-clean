# SENTINEL-3B — Captured-Request Verification Method

The original Sentinel-2 RC2 requests were captured from the frozen applications in a headless browser. Sentinel-3A proved that RC2.1 changes only tutor prompt/build-identity surfaces; request routing, model, token limits, message construction, backend endpoint, local safety functions, storage, and fetch signatures are unchanged.

This environment blocks Chromium navigation to local/file URLs, so Sentinel-3B does not pretend to have performed a new browser interception. Instead it reconstructs the RC2.1 production-format payloads from the exact Sentinel-2 browser-captured RC2 payloads by applying the authorized RC2→RC2.1 system-prompt transformation only.

The reconstruction is independently checked against the actual RC2 and RC2.1 prompt constructors under the same controlled neutral-state stubs used by Sentinel-3A. For both Examined and Navigator, transforming the RC2 constructor output yields the RC2.1 constructor output byte-for-byte. The 47 backend pairs therefore differ only in `system`; the two local Navigator P06-A records remain identical local interruptions.

This establishes exact production-format request reconstruction under the Sentinel-3A minimal-diff boundary. It does not establish live language-model behavior.
