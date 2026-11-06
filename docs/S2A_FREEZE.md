# Phase 1.4 S2a Freeze Record

**Date:** 2026-11-06
**Status:** Reviewer r2 re-review recommends freezing S2a. This record fixes the
baseline and scope; it is not an independent execution certification of the
local repository.

**Evidence level:** The Reviewer examined the supplied diffs, key source, two
negative tests and three audit JSONs. No independent checkout, test run or full
Git object verification was performed by the Reviewer.

## 1. Frozen baseline

| Item | Value |
| --- | --- |
| Final HEAD | `89ac0cd8926aef3ffdf4cfaba84c1c8bde5938ef` |
| S1 frozen commit | `3fc45195d8da20d95dd30ef87ef19859d3d2e002` |
| S1 `rule_primitives.py` SHA-256 | `49e85b601e405b05e585c05a38030b6116b1002e78dab4c2156786ee5a279ab6` |
| TableParams SHA-256 | `82d4df4d1cb3cac9741831b0db36e19fa80c1829abc18b3f8b1ab4ee1c6b9f0a` |
| Parser config SHA-256 | `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` |
| Visual parameters | `visual_min_rule_span_pt=4.0`, `visual_boundary_tol_pt=2.5`, `visual_full_height_coverage=0.85` |
| Test report | `159 passed, 2 xfailed in 12.18s` |
| Primitive audit | 3 samples, all `0 issues` |

Implementation chain (single line, `4246c41` is the initial test-only commit):

```text
4246c41 test  -> 9571756 docs -> ff38d2e fix -> 6962126 docs
        -> d02e690 fix -> a59c105 docs -> 432cf4a fix -> 89ac0cd docs (HEAD)
```

Final implementation commits: `ff38d2e` (identity + primitive rebuild),
`d02e690` (tolerance binding + required artifacts), `432cf4a` (GRID_TOL bound
to the frozen S1 file hash), `89ac0cd` (HANDOFF).

## 2. Scope confirmed frozen

- Visual status set: `{not_printed, partial, implied_outer, printed}`. This is
  not a progression chain; the exact decision precedence is the P1 rule in
  `docs/PHASE1_4_S2A.md`.
- P1 status precedence: r1 conclusion retained.
- P2 segment evidence and raw-primitive authenticity: closed by r2 materials.
- P3 deterministic anchor grouping: r1 conclusion retained.
- P4-1 `GRID_TOL` frozen-baseline binding: closed.
- P4-2 required-artifact completeness: closed.
- Per the supplied S1/S2a diff report, no change was found in S1 physical
  rules, Gold v1/v2, the physical lattice (`grid.xs`/`grid.ys`), cell bbox/text,
  Candidate IDs or any visual threshold. This freeze record does not claim those
  zero diffs were independently re-verified.

The S1 binding covers `src/icpdf/parser/rule_primitives.py` only, not the whole
S1 repository tree.

## 3. Known limitations (not resolved by the freeze)

1. `DS10CP152-P03-T01`: Gold `partial` vs predicted `printed`; measured
   coverage 0.952 against threshold 0.85.
2. Visual status accuracy remains 18/19, not 19/19.
3. Logical columns remain 18/21; S2a does not solve logical column boundaries.

No threshold was tuned against the frozen Gold to hide these differences.

## 4. Not authorized

- S2b (logical boundary lattice / projection).
- S2c (`ConditionContext` / `ConditionBand`).
- Product Identity Resolution.
- Any Codeup push.

S2b requires a separate design submission and review before implementation.

## 5. References

- `docs/PHASE1_4_S2A.md` — full S2a evidence bundle.
- `HANDOFF.md` — implementation ledger.
- `runs/phase14_s2a/review_r2/packet/` — diffs, audit JSONs, S1 baseline note.
- `tools/audit_visual_primitives.py` — read-only audit (not the formal
  validator).
- `tests/integration/test_phase14_primitive_audit.py` — 13 audit tests.
