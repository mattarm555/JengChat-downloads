# Two-version pilot

Share the Pages link with one Windows friend first. The baseline pilot installer
uses /pilot/source.txt; the update target uses /updates/ for future releases.
Both releases retain complete checksums, release metadata and matching source.
Pilot artifacts use separate -pilot GitHub tags and development=true metadata;
the normal production publisher rejects them.

The pilot workflow verifies every public asset before deploying the page and
isolated feed. It does not create a normal update feed. After the friend reports
success, release the reviewed source as a normal version at least as new as the
pilot target, and run the production promotion workflow. No extra folder or ZIP
replacement is needed by the tester.

Collect: Windows version, installed version before/after update, decline/reopen,
successful restart, preserved settings, sign-in/chat/multiplayer smoke checks,
and offline chess/Stockfish review. Do not collect passwords. Record each check separately. The user confirmed second-machine install/update and
waived its settings check for beta 2; other unreported checks remain unverified.
For 3.0.0-beta.1 (Raylib to Godot) the owner waived the second-machine pilot and
settings check on 2026-11-22. The owner installed it on their own PC, and the
local `verify_updates.py` (13/13) and `verify_raylib_migration.py` (6/6) passed,
but no second machine has installed or updated it.
For 3.0.0-beta.2 the owner waived the second-machine pilot and settings check on
2026-11-25. The local `verify_updates.py` passed 13/13 on development builds of
the same source; no second machine has installed or updated it. Later versions
need the pilot again.
Production deployment must retain pilot/source.txt as a pointer to the normal release.
