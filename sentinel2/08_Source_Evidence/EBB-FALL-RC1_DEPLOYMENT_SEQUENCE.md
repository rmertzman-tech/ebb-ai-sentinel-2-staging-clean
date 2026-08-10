# EBB Fall 2026 RC1 - Deployment Sequence

1. Archive the current GitHub repository state and confirm both rollback ZIPs open.
2. Deploy Examined RC1 to a temporary test repository or branch. Verify the `examined-build` meta value is `examined-fall-2026-rc1`.
3. Run the full-record restore fixture, Navigator export fixture, one live ordinary Companion response, and one long-response continuation.
4. Deploy Navigator RC1 to a temporary test repository or branch. Verify the `navigator-build` meta value is `navigator-fall-2026-rc1`.
5. Run PRF import, Examined merge twice, support panel, live Twin, checkpoint, Reflection Export, install/update, and offline tests.
6. Complete the device/browser, Canvas, accessibility, crisis/false-positive, and sync rows in the launch workbook.
7. Promote to the student URLs only after every launch-blocking row is PASS or has an explicitly approved fallback.
8. Freeze code. Make only documented P0/P1 hotfixes during the term.
9. Keep the two rollback ZIPs outside the live repositories.
