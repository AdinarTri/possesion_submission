# Provenance and rule boundaries

Specification: local organiser repository `more-than-a-hack-2027`, revision `f8f2629ff1e0985f81d7e59d8413678514ee1530`; CHALLENGE.md, DATA.md, SUBMISSION.md, RULES.md, FAQ.md and EVALUATION.md. User-supplied restrictions on video comparison and game-based training/tuning take precedence over broader permissions in the repository.

- Inference reads only three permitted original automatic assets, locally.
- No video, image, frame crop, public/private ground-truth CSV, human event data, or prior experimental output is opened by inference or tests.
- No training, fitting, calibration, parameter sweep or score-based method selection.
- Heuristic constants were fixed before execution. They are not externally validated or optimised.
- Synthetic tests contain invented generic cases, not annotations of this game.
- No external training dataset; no external data licence is needed for inference. Match assets remain subject to the participant's competition terms.
- No match data is uploaded by this pipeline, embedded in code, or copied to this repository. The code has no network client. This statement is scoped to the new pipeline, not the earlier session described below.
- Prior work in sibling folders includes visual reviews and video-based calibration performed before this submission task. Those artifacts are excluded; this is not a claim that the entire earlier workspace followed the current restrictions. No prior calibration or labels are dependencies of the submission.
- Public code must not include source tracking, clips or reconstructive intermediate data. Git ignores artifacts and match formats. The CSV is a separate form attachment.
- No repository push, form submission, email or message to organisers has been performed.

The organiser FAQ prohibits sending restricted match data or extracts to third-party hosted LLMs. Raw assets were inspected through assistant tools earlier in the wider session before this FAQ was read; this cannot be undone or represented as never having happened. Subsequent submission processing stays local and returns only operational check results. This disclosure does not decide eligibility; only the organisers can do so.

The official validator confirms the file contract only. No performance or eligibility approval is inferred from passing it.
