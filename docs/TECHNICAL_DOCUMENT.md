# Causal control-state possession inference

## Task and approach

This submission assigns H (home/Barcelona), A (away/Athletic Club), D (dead ball), or X (abstention) to all 199,319 frames of the tactical recording. The method is a deterministic, causal state machine using sustained player–ball proximity. It requires no training, optimisation, video decoding or external model. It is designed to avoid interpreting a brief opponent touch or missing ball detection as a possession change.

This is an untuned heuristic, not a claim to beat the published baseline. Neither public nor private ground truth was used to select it, set constants, or measure its accuracy. The competition's ranking metric is spellF1; no spellF1 or macroF1 result is claimed here.

## Inputs and alignment

Only the original tactical ATD metadata XML, ATD text and automatic Smart Tagging XML are read. Home and away IDs come from the metadata Score element. Player channel references determine the slot order; slots are never treated as persistent player identities or jersey numbers. Normalised coordinates are scaled by metadata pitch dimensions (105 by 68 metres).

ATD frame ID minus one gives the submission frame. Tag seconds are converted with round(seconds × 25) and treated as half-open intervals. The published half blocks from DATA.md delimit processing; state resets between halves. X is written outside them. These are published task boundaries, not newly annotated events. No match-specific possession transitions or kickoff labels are hard-coded.

Neither video, homography nor broadcast data is opened. Broadcast has a separate time base; no alignment is estimated. Prior overlay experiments, manually interpreted jersey candidates, detector outputs, speed analyses, and video-derived calibration are excluded. They are not imported or copied into this repository.

## Evidence and possession rules

For each frame with a finite ball coordinate inside the pitch, the closest valid track from each team is found in metre space. Both teams must have at least one usable track. A control candidate requires distance at most 2 m and a lead of at least 0.5 m over the closest opponent. These are untrained engineering assumptions, not measurements established from this game.

Automatic attacking phase codes support the tagged team; defensive phase codes support the opposite team. Support is boolean per team, so BALL IN FINAL THIRD and BALL IN THE BOX appearing together do not create two votes. If exactly one team has support and it contradicts the proximity candidate, that candidate is withheld. Conflicting or absent tag support supplies no veto. PLAYERS IN THE BOX, GOALS and SET PIECES do not directly label possession: their intervals are not exact control or dead-ball boundaries.

A candidate must persist for 1 second (25 consecutive frames) to set or switch possession. The previous state remains until confirmation. No retrospective relabelling occurs, so transitions have up to about one second of confirmation latency. A transient touch, an ambiguous duel, or a loose ball retains the last state. This approximates the challenge's controlled-possession rule but cannot establish intent or actual touches.

An observed ball outside the normalised pitch for 0.5 seconds (13 frames after rounding up) sets D. A return inside alone does not end D: confirmed control is required. This detects some boundary stoppages; it does not detect the referee's whistle, fouls inside the pitch, offside, or the legal instant of a restart. Ball-centre coordinates also do not establish whether the whole ball crossed the line.

Missing ball or missing coverage of either team retains the last state for at most 2 seconds; after that the emitted label is X. Missing coordinates are never interpreted as D and never filled with invented positions. Internal state remains available for continuity when observations resume. Prolonged visible loose-ball situations retain the last state without a timeout, which is an explicit limitation.

## Training, parameters and provenance

No labelled dataset, external dataset, pretrained model or training process is used. No parameter search, fitting, calibration, or comparison against the provided video is performed. Constants in config.json were fixed before the first inference run and were not changed based on this match's outputs or any score. They remain unvalidated assumptions; any future tuning must use permitted external data with an inspected licence. Synthetic unit-test scenarios test code behaviour only and are not labels for the provided game.

The published task contract supplies frame count, frame rate, label meanings and half boundaries. Physical pitch dimensions and team membership come from the provided automatic metadata. The shorter email rules supplied by the user prohibit training/calibration on this game; this implementation obeys that stricter restriction even where repository RULES.md discusses broader unsupervised options.

## Validation and reproducibility

Tests cover confirmation, deflections, missing values, dead-ball recovery, reset, tag conflict, nested-tag deduplication, geometry and CSV indexing. Validation uses no video or ground truth. The writer rejects malformed input, nonconsecutive frame IDs, incorrect slot counts and incorrect output row counts. SHA-256 of all three inputs is compared before and after inference. A second complete generation checks byte-for-byte reproducibility. The organiser's validator is also run; it checks format, not correctness of possession labels.

CPython 3.10.6; standard library only. From the repository root:

```text
python -m unittest discover -s tests -v
python src/possession.py --data /path/to/dataset
```

The result is artifacts/possession.csv and a manifest of hashes and aggregate diagnostics. No randomness, network requests or timestamps affect the CSV. Inference is O(frames × track slots), with O(frames) storage for tag support and streaming tracking parsing.

## Limitations and next work

Proximity is not proof of control; airborne balls, tracking errors, duplicated slots and wrong team membership can defeat it. Confirmation may miss rapid changes and delays transitions. Missing observations cause abstention, and retained internal state can become stale. Automatic tags can suppress a correct transfer. Dead-ball inference is particularly incomplete: in-pitch stoppages and long missing-ball stoppages are not reliably classified. A player holding a stationary ball before a restart can be mistaken for live control. None of these limitations was corrected by watching the supplied game.

The next development step is evaluation and tuning on a licensed external dataset with controlled-possession and ball-in-play labels, especially restart detection. This has not been performed. The submitted file is structurally valid and reproducible; its possession accuracy remains unmeasured.
