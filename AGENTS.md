# AGENTS

## Setup and Verification
- Run `./tools/op.sh setup` before relying on local verification or CI parity.
- Use `scripts/lint/lint.sh ruff --fast` for the existing repo lint path.
- Use `python3 scripts/check_shipping_branch.py` as the canonical quick check for shipping branches.
- On Windows, `py -3.12 scripts/check_shipping_branch.py` is the equivalent local command.

## Code Map
- Subaru controller logic lives in `opendbc_repo/opendbc/car/subaru`.
- Fork-owned UI surfaces live in `selfdrive/ui/sunnypilot`.
- Shared onroad renderers live in `selfdrive/ui/onroad` and `selfdrive/ui/mici/onroad`.
- Param migrations belong in `sunnypilot/system/params_migration.py`.

## Branch Publishing Discipline
- Shipping branches are mirrored to both `origin` and `openpilot`.
- If `opendbc_repo` changes, push the `opendbc` branch first and then update the superproject pointer.
- Keep unrelated dirty worktree files out of release commits and release pushes.

## Param Conventions
- Prefer positive, directly readable param names.
- Do not invert stored booleans in UI bindings.
- When renaming params, update `params_migration.py` and metadata in the same change.
- When removing a user option, remove dead runtime plumbing instead of silently ignoring arguments.

## Windows Note
- Local pytest may still hit the known `openpilot.common` bootstrap/import issue.
- CI on the shipping branches is the authoritative full check for published pushes.
