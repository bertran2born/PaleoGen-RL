# PaleoGen-RL

Goal: reproducible discovery and comparison of population-genetic models, not reward-only optimization.

## Map
- `docs/milestones/`: outcomes and DoD.
- `docs/TSE_ISSUE_STANDARD_v1.md`: issue contract; `docs/issues/`: issues (proposed).
- `reich_experiment_v2/`: simulators, tests, Nix environment.
- `reich_study/`: research sources; read-only.

## Rules
- Inspect the relevant milestone, standard, and nearby code before editing; search narrowly.
- Solve one scoped issue at a time; avoid unrelated refactors.
- Preserve provenance, reference behavior, seeds, and scientific assumptions.
- Never change observations or scoring to improve results; distinguish simulation from evidence.
- Do not alter third-party source or redistribute it without authorization.
- Mark DoD complete only with verification; report blockers and limits.
- Once all Issue DoD criteria are verified, commit its scoped changes. Do not push without explicit instruction.

## Validate
- Run focused tests, then from `reich_experiment_v2/`:
  `nix develop -c python -m unittest discover -s tests`
