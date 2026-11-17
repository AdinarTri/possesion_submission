# Validation record

Environment: Windows, CPython 3.10.6. Date: 2026-11-16.

- Six synthetic unit tests: passed.
- Full original tactical input parsed without padding, truncation or frame reindexing fixes.
- Built-in output contract: passed, 199,319 data rows, frame 0 through 199318, header frame,label, labels restricted to H/A/D/X.
- Organiser validator: passed. Full local output in artifacts/official_validation.txt, excluded from Git.
- Input SHA-256 before and after inference: identical for all three consumed files.
- CSV reproducibility: run twice from the original inputs and compared using tools/check_reproduction.py; see the local reproduction_check.txt result.

No video-output comparison, public/private ground-truth scoring, or parameter tuning was used. These checks verify implementation and file integrity only; they do not establish possession accuracy. Tests of the state machine use synthetic sequences, not manually created labels for the supplied game.

Both inference runs used the same config and source; no parameter variants were generated or selected. Runtime writes only to the separate artifacts directories. The current repository has no configured remote, no publication and no submission to the competition form.
