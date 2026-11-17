# Possession submission

Local, reproducible entry for More than a Hack 2027 Phase 1. Produces one `H`, `A`, `D`, or `X` label per tactical video frame. This is an **untuned heuristic submission**, not a verified measure of possession accuracy.

## Reproduce

Tested with CPython **3.10.6**. Inference and tests use only the standard library: no installation, pretrained weights, external datasets, GPU, API keys, or network access required.

From this repository directory:

```powershell
python -m unittest discover -s tests -v
python src/possession.py --data "../More Than A Hack 2027 - Initial Challenge - Dataset"
```

`--data` is the folder containing `tactical/`. Required inputs are exactly one `*atd.xml`, `*atd.txt`, and `*smart_tagging.xml` in that folder. File names are resolved locally; no match assets belong in this repository.

Outputs:

- `artifacts/possession.csv`: exact header `frame,label`, 199,319 rows indexed 0–199318.
- `artifacts/manifest.json`: input/code/config/output SHA-256, aggregate diagnostics, and input-integrity result. It contains no coordinates or video frames.

Repeat into a different directory to check byte reproduction:

```powershell
python src/possession.py --data "../More Than A Hack 2027 - Initial Challenge - Dataset" --output artifacts/reproduced
python tools/check_reproduction.py artifacts/possession.csv artifacts/reproduced/possession.csv
```

The built-in validator runs before publishing the CSV. Also run the organiser's official validator against the exact file:

```powershell
python ../more-than-a-hack-2027/evaluation/validate_submission.py artifacts/possession.csv
```

That optional validator needs the organiser's environment (`numpy`/`pandas`); neither is used by inference. Structural validity does not establish accuracy. No ground-truth evaluation or video comparison is part of this workflow.

## Repository

```text
config.json                  frozen, untrained heuristic settings
src/possession.py            parser, evidence extraction, causal state machine, writer
tests/test_pipeline.py       synthetic tests, no match-specific labels
tools/check_reproduction.py  CSV equality check
docs/TECHNICAL_DOCUMENT.md   short submission document in English
docs/DATA_HANDLING.md        missing values and handling decisions in Indonesian
docs/COMPLIANCE.md           provenance and exclusions
artifacts/                  local outputs, ignored by Git
```

The algorithm uses sustained proximity as a control proxy, holds possession through loose balls, abstains on prolonged missing observations, and detects some dead balls through sustained out-of-pitch ball coordinates. Automatic phase tags veto contradictory control evidence; nested tags do not count as independent votes. Details and limitations are in the technical document.

## Submission preparation

Submit `artifacts/possession.csv`, `docs/TECHNICAL_DOCUMENT.md`, and the URL of this code repository after publication. The organiser asks that uploaded filenames use the registered team name: rename copies for upload, without editing the CSV contents. The team name has not yet been supplied.

No remote is configured and nothing is pushed by these instructions. `artifacts/` is deliberately excluded from Git, as are match assets. Upload the CSV directly through the competition form; publish source and documentation only. Local compliance checks are not an eligibility guarantee from the organisers.

Specification reference: local `more-than-a-hack-2027` at commit `f8f2629ff1e0985f81d7e59d8413678514ee1530`. No source code or match assets from that repository are copied into this implementation.
