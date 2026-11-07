# Phase 1.4 S2b — Logical Boundary Lattice and Projection

**Status:** design proposal only (revision r15, a revision of r14; based on
`6f3e58d` plus the additive code slice recorded in §3.1, §5.6, §5.7 and §7.3).
r15 carries design text only: it merges the group 1, group 2 and batch-5
rulings recorded in §1 and adds no code, schema, Gold or threshold change. No
implementation, schema change, Gold change or pipeline integration is
authorized by this document. Implementation starts only after the Reviewer
closes the items in §1.

**Relationship to the approved S2 design:** `docs/PHASE1_4_S2.md` remains the
umbrella design. S2b narrows its §5–§7 to the logical column lattice and the
physical→logical projection. Where this document is more specific, it is a
proposal for review, not a replacement of the approved principles.

## 1. Review resolution map

This revision answers the seven review items and the P0/P1 findings on
`cf59799` (r2), the eight blocking findings in the r2 re-review, the four
residual ambiguities found in the line-by-line r3 review, the three
lexical/group defects found in the r4 review, the N6 reconstruction gap found
in the r5 review, the hyphen-rule ambiguity found in the r6 review, the
classification contradiction plus the two evidence-transport defects found in
the r7 review, and the `kind` misreading and second transport loss found in the
r8 review, the four N7/N8 closure items found in the r9 re-review, the five
residual constraints in the r10 re-review, and the two remaining boundaries in
the r11 re-review, and the batch-5 findings on D7, D14–D16 and the T1–T26
matrix that this r15 revision closes.
Nothing below is an implementation claim; every repository statement is backed
by a path and line reference in §3.

**r15 review findings (current round).**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R15-B5-D1 | No table-level projection band or `BandObservation` carrier; `row_bands` and band counts used two index spaces without a canonical partition | §5.2 `row_bands`; §5.4 bands; §11 invariants 18 and 20; §13.1 T7/T25 |
| R15-B5-D2 | `LogicalBoundaryDecision.row_bands` was absent, so T7 could not assert retained bands | §5.2 `row_bands`; §5.3; §11.20; §13.1 T7 |
| R15-B5-D3 | Run split, word crossing, rule matching and band word assignment were implementation details with no single normative text | §5.3.1 items 1–4; §11.20; §13.1 T13 |
| R15-B5-D7 | One tie rule was stated three different ways (§5.3, §6.3, §9.2); near-equal runs flipped the decision | §5.3.1 run predicate; §5.2 D13; §6.3 step 3; §11.21; §13.1 T7/T24 |
| R15-B5-D10 | 31 codes included two unreachable and three schema codes; there was no branch-to-code map | §10.2 five namespaces and 27 L codes; closure and branch maps; §11.21 |
| R15-B5-D11 | A and L namespaces mixed; a schema failure could set logical status | §10.1; §10.2 namespaces; §11.0; §11.21(a) |
| R15-B5-D12 | No closure table from branches to codes; `header_ref_ambiguous` was not in any closed set | §10.2 closure; §11.0 row 8.8; §11.21; §13.1 T21 |
| R15-B5-D14 | Keep thresholds existed only in evidence validation; "band" mixed body rows with projection bands; ratio denominators were undefined | §5.2 band definition; §6.1; §6.2 D14 objects; §9.2 ratio; §11.20 |
| R15-B5-D15 | Zero and multiple matches for a header ref had no stable codes; first match was silent | §5.3 header_canopy; §9.2 two-step resolution; §10.2 code 27; §11.8; §13.1 T20 |
| R15-B5-D16 | "Section-like row" had no definition, so a full-width body cell could enter the veto denominator | §5.3.2; §6.2; §8.1; §11.20; §13.1 T22 |
| R15-B5-T | T7/T13/T16/T20/T21/T22/T25/T26 expectations were blocked, wrong, or measured the wrong object | §13.1 |
| R15-B5-OPEN | No geometric gutter predicate exists, and two texts disagree on whether a gutter row may be crossed | §14 item 23 |

**r14 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R14-D8 | Data-cell crossing veto scope diverged between §6.2 (any crossing vs every supported band) and §8.1; "support" was undefined | §5.3 supporting-band and crossed-band definitions; §6.2 rows; §8.1 single veto rule; §11 invariant 20 |
| R14-D9 | `subrule_short_label` required `role = condition` but did not say which logical column receives the role | §5.5 role recipient; matrix row; §11 invariant 13 |
| R14-D13 | `condition_bands` / condition-like text did not say whether the selected nearest right-side run or any run is tested | §5.3 selected-run paragraph; §6.5 precondition and counts; §11 invariant 20 |

**r13 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R13-D4 | `word_boundary_tie` had no defined landing: it must be a validator/runtime count, not a reason code or a persisted assignment field, counting each exact hit once and never making the table unresolved | §7.3 item 2 (outer-extent precondition and tie rule); §10.2 (removed from the code list; diagnostic-count paragraph) |
| R13-D5 | The row-local rank formula and the alignment-grid word capture were design claims without repository evidence | §3.1 (current models); §5.6 (two index spaces and capture); §7.3 (D5 capture facts); §11 invariant 10 |
| R13-D6 | `non-decreasing` contradicted the closed D3 strict-ascending rule; old-artifact load order, artifact-only validation and fresh-parse audit were not separated; `grid.ys` copy wording was wrong | §5.7; §7.3 D6; §11 invariants 16, 18 and 19; §13 |

**r12 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R12-S2BID | The rules did not say whether a non-derived s2b positive may share a physical identity with a v1 positive; the only permitted cross-set reuse must be the declared v2-to-s2b relation | §12.1 D, s2b cross-set row and rule 5; §14 item 22; §15 R11-N7-2 |
| R12-ROOT | A valid JSON root can be an array, string, number or `null`, and `params` can be a non-object; both must be schema-invalid, not an unclassified exception | §5.8, root and `params` object checks; §11 invariant 17; §15 R11-N8LOAD-1 |

**r11 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R11-N7-1 | `(pdf_sha256, page, table_index)` of a positive must not repeat across v1 and v2; a v1/v2 pair describing one physical table counts it twice, and this version has no exception | §12.1 D, cross-manifest physical identity |
| R11-N7-2 | `item_id` uniqueness was scoped to v1 plus v2; it must cover all three manifests, and `derived_from_item_id` is a provenance reference that cannot replace the s2b item's own id | §12.1 D, global id and derivation |
| R11-N8LOAD-1 | A type check on a caller-supplied object does not prove loader origin; the validator must take raw bytes and call the loader itself, and loader failures need distinct codes | §5.8, raw-bytes validator and three failure classes |
| R11-N8LOAD-2 | `snapshot_sha256` hashes canonical JSON, not raw bytes; the stored-value wording claimed otherwise | §5.8, hash semantics paragraph and type rule 2 |
| R11-22 | The §14 item 22 exception needs three constraints: a v2 positive source, fully equal identities, and no multiple s2b ids per physical table | §14 item 22; §12.1 D derivation |

**r10 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R10-N7SET | The 46 / 19 / 21 / 8 arithmetic holds, but set exclusivity, id de-duplication and source identity have no machine-checked constraint | §12.1, manifest identity and merge checks |
| R10-N8VER | The serializer sends every version other than v1 to the v2 field set, so an unknown version can produce a v3-labelled v2 snapshot | §5.8, explicit version dispatch |
| R10-N8LOAD | A plain `dict` cannot hold duplicate keys, so a `dict`-typed validator never sees them | §5.8, `load_table_params_snapshot` and `LoadedTableParamsSnapshot` |
| R10-N8FIELDS | One delivered field name read `merge_column_tol_ptl`; the v1 field set needs verification against `config.py` and per-field type rules | §5.8, field table and type rules; §16.6 records the delivery defect |

**r9 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R9-KIND | `kind` must be `header` for `row_end < header_rows`, `data` for `row_start >= header_rows`, and `logical_cell_kind_boundary` when a cell crosses the header boundary | §5.6 item 1: the r8 text already said this; the `<` was lost in rendering. r9 states it with `≤`/`≥` and a six-row decision table and removes the bare `<` from the rule |
| R9-WORD | "words with no assigned word produce no logical cell" is the wrong subject; the rule is about a physical cell with no word in any logical column | §5.6 item 1, first bullet |
| R9-LOSS2 | The delivered §5.6 and §16 still arrived with lost operators, merged fences and truncated shell commands, so byte-equality could not be checked | §16.6: both sections delivered out-of-band as base64 with SHA-256 |
| R9-ORDER | The comparison script should also reject an end heading that precedes its start heading | §16.2, §16.3 (`line_of`, exit 4), §16.4 |

**r8 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| R8-CLASS | `V-10V` satisfies the `identifier` regex and contains a digit, so the run `5V-10V` cannot be tokens `5`,`V-10V`, accepted by `identifier`, and `unclassified` at the same time | §6.3.1: content classes are run-level, `identifier` is single-token, and its downstream effect is defined |
| R8-LOSS | The pasted §5.6 pseudocode lost `*`, `<=`, and parts of the loop tail, and the pasted §16 script lost `printf`/`wc`/`diff` characters | §5.6 item 3 and §16.3, each with a byte-exact base64 copy and its SHA-256 in §16.6 |
| R8-ANCHOR | `index($0,s)==1` is a prefix test, so `## 12.` also selects `## 12.2`/`## 12.3`; heading matching must be exact | §16.2, §16.3 (`$0==s`), §16.4 |

**r7 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| N5-hyphen | "`-` between two word-class characters" cannot separate `CLK-1` from `5-10`, because digits are word-class | §6.3.1 word-run hyphen rule, test vectors |
| N5-mult | A multiplier must not be extracted from inside a token already matched as a complete unit | §6.3.1 multiplier rule, `10kΩ` vector |
| N6-verify | The pseudocode must be shown equal to `structure.py`, and the full §5.6 text must be delivered without character loss | §5.6 item 3, delivery message |
| N7/N8 | §16 must record both input digests, heading anchors, excerpt sizes, exit codes and per-invariant results | §16 |

**r6 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| N6-text | `LogicalCell.text` still referenced `_words_to_text` without the line-grouping, running-mean and tie rules written into the document | §5.6 item 3 |
| N5-token | Longest-match and sign-context tokenization had no normative test vectors | §6.3.1 |
| N7/N8 | Only a no-touch diff was shown; the full document was not re-verified | §5.8, §11–§13, §16 |

**r5 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| N5-1 | `..` is a range connector but tokenization only splits on "a comparison operator or a range dash"; multi-character operators have no longest-match rule | §6.3.1 |
| N5-2 | The operand grammar is undefined: generic comparison, range and symbol binding do not say which sides must be value-bearing | §6.3.1 |
| N5-3 | The symbol list ends in `…`, so implementations may admit `VIN`, `TEMP`, `CLK` | §6.3.1 |
| S3-span | Requiring each ref to agree with the previous ref still permits chain merging | §5.3, §9.2, §11 |

**r4 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| N2 | Source-cell containment is closed on both ends, so an x that lands on a shared cell edge can match two cells | §5.3, §6.3 |
| N3 | `region_extent` validates a region's internals but never proves that region belongs to this table | §5.3, §9.2, §11 |
| N5 | `short_label` is tested before the relational marker, so `A=B` can never become `condition_expression`; range connectors lack a tokenization rule | §6.3.1 |
| S3 | "At most one ref per `(grid_row, edge)`" contradicts accepting several agreeing refs | §5.3, §11 |

**r3 review findings.**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| N1 | `HeaderCanopyEvidence` has an undirected ref set; the auditor must re-run the left/right decision | §5.3, §9.2, §11 |
| N2 | `SubrulePromotedEvidence` lacks per-band, per-cell word attribution; ratio is not independently recomputable | §5.3, §6.3, §11 |
| N3 | `TableBBoxEvidence` / `RegionExtentEvidence` are only self-consistent, not anchored to a fresh parse | §5.3, §9.2, §11 |
| N4 | Candidate grouping can chain-merge beyond tolerance; no fixed anchor | §6.1, §11 |
| N5 | `condition_path` lexical rule is too broad; ratio definition incomplete | §6.5, §6.3 |
| N6 | `LogicalCell` bbox, id, rowspan/colspan and word-universe reconstruction rules are incomplete | §5.6, §7.3, §9.3, §11 |
| N7 | Gold annotation type and ambiguity overlay are still collapsed into one status | §12.2 |
| N8 | v1/v2 snapshot validation is hash-only; S2a audit edit boundary is undefined | §5.8, §13 |
| S1 | §5.5 "at most one ref" contradicts "both present must agree" | §5.5 |
| S2 | Projection row bands, visual intervals and overlap recomputation are under-specified | §5.4, §7.2, §11 |
| S3 | Structural edge de-duplication, header overlap formula, boundary tie-break, cell kind edge cases | §5.3, §7.3, §8.2, §11 |

**r2 findings (kept for traceability).**

| Item | Question | Answer in |
| --- | --- | --- |
| R1 | Actual repository definitions of `DetectedTable`, `DetectedCell`, `DetectedHeaderCell`, `grid.xs`, `region_components` | §3.1–§3.3 |
| R2 | Gold v2 annotation version, item count, logical fields, and 67 vs 65 | §3.6, §12.1 |
| R3 | How `PhysicalColumnOverlap` locates a physical column across regions | §3.3, §7.1 |
| R4 | Minimum evidence fields per boundary source and validator rejection rules | §5.3, §11 |
| R5 | No-evidence demotion vs condition-path demotion | §6.5 |
| R6 | Preserving `table-params/v1` SHA and S2a audit compatibility | §5.8 |
| R7 | Independently reconstructable physical-cell and word assignment | §5.6, §9 |
| P0-1 | Region-local lattices vs a global `grid.xs` index | §3.3, §7.1 |
| P0-2 | Missing `subrule_promoted` / outer-edge evidence kinds | §5.3 |
| P0-3 | Every demotion incorrectly assigned to `condition_path` | §6.5 |
| P0-4 | `table-params/v2` without version-dispatched serialization | §5.8 |
| P1-1 | Which words of a shared physical cell belong to which logical cell | §5.6, §9.3 |
| P1-2 | Duplicate `projection` / `column_projection` | §5.4, §5.7 |
| P1-3 | Invented role-source vocabulary | §5.5 |
| P1-4 | Ambiguous `visual_columns` index | §5.4 |
| P1-5 | Gold `ambiguous` conflated with algorithm `unresolved` | §12.2 |

## 2. Problem

S2a established that the visual boundary evidence is trustworthy: every
persisted segment resolves to real PDF primitives. S2b addresses a different
question:

> Which printed and structural facts justify treating a boundary as a logical
> column boundary, and how are physical cells projected onto those logical
> columns without changing the physical grid?

The two lattices are not interchangeable. Gold v2 contains tables where logical
columns exceed visual columns (header canopies) and tables where visual columns
exceed logical columns (body condition sub-rules). The current logical count is
18/21 on the 21 typed Gold v2 tables; S2b must make the reasoning explicit and
auditable rather than infer a count from cell content.

Gold v1 (46 tables) does **not** carry typed logical columns. It therefore
contributes physical/S2a/candidate regression data and a set of explicitly
ambiguous cases, but it is not a logical-column ground truth. This distinction
is developed in §3.6 and §12.

Success means:

- every kept logical boundary has at least one allowed, resolvable evidence
  source;
- every logical column carries a traceable physical-column projection using the
  table's one physical lattice;
- every logical cell carries physical cell references and a disjoint per-cell
  word partition;
- undecidable cases fail closed at table level instead of guessing;
- S1 physical fields and S2a visual fields are byte-for-byte unchanged.

## 3. Repository facts (R1, R3)

### 3.1 Actual parser models

These are the current definitions, not proposed models. Excerpts are abridged
to fields only; the source is authoritative.

Code references in this document use `module::symbol`, for example
`icpdf.parser.structure::_assign_words`, and never file line numbers: line
numbers drift between commits and are not normative. A field reference appends
the field to its owner, for example `icpdf.parser.structure::TableGrid.xs`.

`icpdf.parser.table_detector::DetectedCell`:

```python
class DetectedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    bbox: BBox
    column_index: int = Field(ge=0)
    row_span: int = Field(default=1, ge=1)
    column_span: int = Field(default=1, ge=1)
    word_ids: tuple[str, ...] = ()      # D5 additive; no cell identity
```

`icpdf.parser.table_detector::DetectedRow`:

```python
class DetectedRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    bbox: BBox
    cells: list[DetectedCell]
    grid_row: int = Field(default=0, ge=0)
```

`icpdf.parser.table_detector::DetectedHeaderCell`:

```python
class DetectedHeaderCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    level: int = Field(ge=0)
    column: int = Field(ge=0)
    text: str
    bbox: BBox
    source_row: int = Field(ge=0)
    source_column: int = Field(ge=0)
```

`icpdf.parser.table_detector::DetectedTable`:

```python
class DetectedTable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    page_number: int = Field(ge=1)
    bbox: BBox
    title: str | None = None
    table_type: TableType = TableType.UNKNOWN
    headers: list[str] = Field(default_factory=list)
    header_rows: int = Field(default=0, ge=0)
    header_path: list[list[str]] = Field(default_factory=list)
    header_cells: list[DetectedHeaderCell] = Field(default_factory=list)
    column_roles: list[str] = Field(default_factory=list)
    rows: list[DetectedRow] = Field(default_factory=list)
    detection_method: str = "text_alignment"
    confidence: float = Field(ge=0.0, le=1.0)
    reconstruction_status: ReconstructionStatus
    uncertainty_reason: str | None = None
    region_components: list[int] = Field(default_factory=list)
    boundary_source: str = "ruled"
    merge_evidence: list[str] = Field(default_factory=list)
    # Phase 1.4 S2a - derived visual lattice; never affects the physical grid.
    visual_boundaries: tuple[float, ...] = ()
    visual_boundary_status: str = "unknown"
    visual_columns: int | None = None
    partial_boundaries: tuple[float, ...] = ()
    visual_boundary_evidence: tuple[VisualBoundary, ...] = ()
    # Phase 1.4 S2b (D6) - physical lattice copied verbatim; never affects the grid.
    grid_ys: tuple[float, ...] = ()
    n_rows: int = Field(default=0, ge=0)
```

Consequences that the design must respect:

- `DetectedCell` has **no** `cell_id`; its parser-level identity is
  `(DetectedRow.grid_row, index within DetectedRow.cells)`. `word_ids` is
  additive payload, not identity.
- `DetectedHeaderCell` has **no** `header_cell_id`; its parser-level identity is
  `(level, column, source_row, source_column)`.
- `DetectedTable` does **not** persist `grid.xs`. It persists `grid.ys`
  verbatim as `grid_ys` plus `n_rows` (D6), and each `DetectedCell` carries
  its assigned `word_ids` (D5). `grid.xs` still exists only in the
  intermediate `TableGrid` during `detect_tables()`.
- `DetectedRow.cells` holds only non-empty cells of one grid row, in flat
  `TableGrid.cells` order; the flat index is **not** recoverable from the
  row-local position when empty cells precede it. See §7.3 for the two index
  spaces.
- `DetectedTable.column_roles` is the existing per-physical-column role list
  from `infer_semantics`; S2b logical roles must not overwrite it.

Domain models add ids during rebuild (`src/icpdf/parser/table_rebuilder.py`):

- `table_id = f"p{page:03d}-t{table_index:02d}"`;
- `row_id = f"{table_id}-r{row_index:02d}"`;
- `cell_id = f"{row_id}-c{column:02d}"`;
- `header_cell_id = f"{table_id}-h{level:02d}-c{column:02d}"`.

### 3.2 `grid.xs` is one lattice per detected table

`grid.xs` is `icpdf.parser.structure::TableGrid.xs`, not a field of
`DetectedTable`:

```python
@dataclass
class TableGrid:
    bbox: BBox
    xs: list[float]
    ys: list[float]
    cells: list[GridCell] = field(default_factory=list)
    unassigned_words: list[TextWord] = field(default_factory=list)
    source: str = "rule_lattice"
```

`icpdf.parser.table_detector::detect_tables` builds exactly one grid per
region:

```python
for region in detect_table_regions(layout, params):
    grid = recognize_structure(layout, region, params)
    ...
```

`icpdf.parser.structure::recognize_structure` delegates to
`icpdf.parser.structure::_rule_grid` or
`icpdf.parser.structure::_alignment_grid`. `_rule_grid` creates one `all_xs`:

```python
all_xs = _unique(edges + hard_xs + header_candidates + soft_xs, 4.0)
```

and one `TableGrid(bbox, all_xs, ys, cells, source=region.source)` at the end
of the same function. `icpdf.parser.structure::_alignment_grid` likewise
creates one `xs` list. There is no per-row or per-component x lattice.

`icpdf.parser.structure::GridCell` is:

```python
row, column, row_span, column_span, bbox, text="", word_count=0
```

It does not retain word ids. `icpdf.parser.structure::_assign_words` assigns
each `TextWord` by center to one cell and then discards the list after setting
`cell.text` and `cell.word_count`. S2b must therefore capture word ids in the
same pass or recompute the same deterministic assignment; §9 defines the rule.

### 3.3 `region_components` is provenance, not a second lattice

`src/icpdf/parser/table_regions.py` merges stacked components into one
`TableRegion`. `icpdf.parser.table_regions::_merge_pair` requires shared
column rules, a minimum shared ratio, horizontal-extent alignment and no
caption in the gap (`TableParams.merge_*`).
`icpdf.parser.table_regions::_region_from_cluster` then builds one region and
`icpdf.parser.table_regions::_union_component` unions the members' segments
into one `RuleComponent`. `_region_from_cluster` also emits structured
`RegionEvidence` with kinds `merge`, `absorbed` and `implied_outer`.

`DetectedTable.region_components` is filled in
`icpdf.parser.table_detector::detect_tables`:

```python
region_components=[component.component_id for component in region.components]
```

It records which components contributed to the one region that produced the
table. It does **not** select a per-region x lattice, and it cannot be used to
reinterpret `physical_column`.

`icpdf.parser.structure::TableRegion` and
`icpdf.parser.structure::RegionEvidence` are:

```python
@dataclass(frozen=True)
class RegionEvidence:
    kind: str
    detail: str
    component_ids: tuple[int, ...] = ()
    values: tuple[float, ...] = ()

@dataclass(frozen=True)
class TableRegion:
    page_number: int
    bbox: BBox
    source: str                       # "rule_lattice" | "text_alignment"
    component: RuleComponent | None = None
    rows_words: tuple[tuple[TextWord, ...], ...] = ()
    components: tuple[RuleComponent, ...] = ()
    boundary_source: str = "ruled"    # ruled | implied_horizontal |
                                      # implied_alignment | mixed
    evidence: tuple[RegionEvidence, ...] = ()
```

`DetectedTable` persists only `region_components`, `boundary_source` and
`merge_evidence` strings, not the structured `RegionEvidence`. S2b therefore
cannot recover an `implied_outer` extent from an old artifact; it must persist
the extent at derivation time (§5.3) or fail closed.

### 3.4 Header cells and role provenance

`icpdf.parser.header_semantics::HeaderCellRef` is:

```python
level: int
column: int
text: str
bbox: BBox
source_row: int
source_column: int
```

The existing `icpdf.domain.candidate::Candidate` role fields are:

```python
column_role: ColumnRole = ColumnRole.UNKNOWN
role_source: str = "unknown"
role_header_cell_id: str | None = None
```

`icpdf.parser.candidate_registry::build_candidates` uses exactly three values
for `role_source`:

```text
"header_text"   role equals the role derived from a printed header
"heuristic"     role came from a documented layout heuristic
"fail_closed"   no evidence; role is UNKNOWN
```

`icpdf.domain.candidate::ColumnRole` values are `min`, `typ`, `max`, `value`,
`condition`, `unit`, `symbol`, `unknown`.

### 3.5 Word ids

`TextWord.word_id` is deterministic
(`icpdf.parser.text_blocks::extract_text_blocks`):

```python
f"p{page_number}-b{block_index}-l{line_index}-w{i}"
```

Spans use `...-s{span_index}` in the same function. Word ids are page-level and
stable for the same PDF, page and text extraction parameters. They are not
stored on `DetectedCell`; S2b must persist the ids it assigns.

### 3.6 Gold artifacts: versions, counts and logical fields (R2)

The repository contains two separately frozen Gold sets:

| Set | Manifest | `annotation_version` | Items | Tables | Negatives | Typed logical field |
| --- | --- | --- | --- | --- | --- | --- |
| Phase 1.2 | `gold/manifest.json` | `gold-2026-11-06.1` | 65 | 46 | 19 | no |
| Generalization v2 | `gold/generalization/manifest.json` | `gen-2026-11-06.2` | 29 | 21 | 8 | yes |

- `gold/versions/gold-2026-11-06.1/VERSION.json` fixes the v1 snapshot at source
  commit `b8c2d3bdf7b1b0900c6ad2204400b80a32dfdead`.
- `gold/generalization/versions/gen-2026-11-06.2/VERSION.json` fixes the v2
  snapshot at source commit `ee456ab2c6484649bddcac2a9217087c3a164190`.
- Both use `schema_version: gold-schema/v1`; the annotation version, not the
  schema version, distinguishes them.
- v1 tables have no `logical_columns`, `visual_columns`,
  `visual_boundary_status` or `partial_boundaries` keys at all.
- All 21 v2 tables have a non-null `logical_columns`, plus `visual_columns`,
  `visual_boundary_status` and `partial_boundaries`. No v2 table sets
  `logical_columns: null`.
- v2 table `column_boundaries` is documented as the logical column boundaries
  used for cells (`docs/GOLD_SPEC.md:48`); `visual_columns` is the count of
  printed visual intervals, `null` for `not_printed`.

**Why 67 and 65 are both correct:**

- `65` is the v1 item count: 46 tables + 19 negatives in one manifest.
- `67` is the count of positive tables across both sets: 46 + 21. The S2a
  physical-diff report uses "67 / 67 gold items" in this sense
  (`docs/PHASE1_4_S2A.md:570-572`). It is **not** a manifest item count and it
  excludes the 27 negatives (19 + 8).
- Only the 21 v2 tables carry typed logical annotations. The earlier sentence
  "Gold v2: 67 items, 21 with a decided logical mapping" conflated the 67
  positive tables with the 21 typed v2 tables. The correct statement is:
  "67 positive tables in the regression pool; 21 of them have typed logical
  columns; the 46 v1 tables are untyped for logical metrics."

The existing evaluator uses `gold_table.get("logical_columns", gold_columns)`
in `goldset.evaluate::_score_pair`, so a v1 table falls back to its legacy
`n_columns`. That fallback is a compatibility behavior for historical reports.
It is **not** an annotation decision and S2b must not use it as one (§12.2).

### 3.7 Gold ambiguity is narrative, not a typed field

No Gold item has an `ambiguous` boolean or enum. In v1 the open ambiguities are
recorded in `review.independent_review_note`, for example:

- `ADS1299-P37-T01`: "Gold merges the partial Either-input band ... (open
  ambiguity 1)."
- `ADS1299-P70-T01`: "Gold keeps the partial band as a fifth column ... (open
  ambiguity 1)."
- `LM358-P04-T01`: "Gold encodes the partial Either-input band as two condition
  columns ... (open ambiguity 1)."
- `LM358-P04-T02`: headerless condition column; the parser's `UNKNOWN` is
  described as annotation debt, not a Gold error.
- `ADC12DJ5200-P46-T01`: leading `SYSREF` column role differs between Gold
  (`VALUE`) and the parser's leading-column heuristic (`SYMBOL`).

v2 (`gen-2026-11-06.2`) contains no "ambiguity" text in its item records. The
five examples above are v1 tables and are therefore also `untyped_legacy` for
logical metrics. §12.2 defines a read-only overlay that preserves their
identity without editing Gold.

## 4. Hard constraints

S2b must not:

- change `grid.xs`, `grid.ys`, physical cell bboxes/text, `column_index`,
  `row_span`, `column_span`, cell ids, Candidate ids or candidate identity;
- re-interpret or overwrite S2a `visual_*` fields;
- add a boundary because a target column count, a Gold value or a desired
  extraction result suggests one;
- use an LLM to propose, rank or select logical boundaries;
- change Gold v1/v2 or tune existing visual thresholds;
- create a second physical lattice, a per-region x renumbering, or a
  cross-table logical merge;
- treat a Gold `n_columns` fallback as a logical annotation;
- implement S2c (`ConditionContext` / `ConditionBand`), section-band semantics or
  Product Identity Resolution;
- push to Codeup.

S2b is an additive, derived annotation. The physical table remains the only
source of cells, text and candidates.

## 5. Data model (deliverable 1)

All proposed models are frozen Pydantic models. Parser-level models live beside
`DetectedTable`; domain models mirror the same fields in `domain/table.py`.
Field names below are proposals, not existing repository fields.

### 5.1 Enums

```text
LogicalMappingStatus = "resolved" | "unresolved"

LogicalBoundaryRole = "outer_left" | "outer_right" | "internal"

LogicalBoundarySource = "printed_rule" | "header_canopy" | "label_aligned"
                      | "structural" | "subrule_promoted"

LogicalBoundaryDecisionKind = "keep"
                            | "demote_no_evidence"
                            | "demote_condition_path"
                            | "unresolved"
```

`logical_mapping_status` is table-level. A legacy table or a table with no
decidable logical lattice is `unresolved`, not a third silent state.

The decision kind split is mandatory (P0-3): `demote_no_evidence` makes no
semantic claim; `demote_condition_path` is reserved for internal partial
sub-rules that meet the condition criteria in §6.5.

### 5.2 `LogicalBoundary` and `LogicalBoundaryDecision`

```text
LogicalBoundary
  x: float
  role: LogicalBoundaryRole
  sources: tuple[LogicalBoundarySource, ...]   # non-empty, sorted
  visual_boundary_index: int | None            # index into the parallel S2a tuples
  visual_coverage: float | None                # copied from S2a, never recomputed
  evidence: tuple[LogicalBoundaryEvidence, ...]  # non-empty
```

`DetectedTable.logical_boundaries` keeps the existing S2 interface type,
`tuple[float, ...]`, and holds the kept x positions in sorted order. The richer
records live in `logical_boundary_detail`, ordered identically; this avoids
changing the approved umbrella field type while keeping the evidence available.
Demoted and unresolved candidates are recorded separately in
`logical_boundary_decisions` so the decision remains auditable without
polluting the accepted lattice.

```text
BoundarySupport
  band_count: int              # body rows in the table, n_rows - header_rows
  rule_bands: int              # body rows with a printed rule at x
  gutter_bands: int            # body rows with a body gutter at x
  supported_bands: int         # distinct body rows with rule or gutter
  supporting_bands: int        # body rows whose evidence backs the candidate (veto denominator)
  crossing_bands: int          # supporting body rows crossed by a body data cell or word
  short_label_bands: int       # body rows whose selected right-side run is a short label
  condition_bands: int         # body rows whose selected right-side run is condition-like
  nonempty_bands: int          # evidence-specific body-row denominator, see below
  support_ratio: float | None  # supported_bands / nonempty_bands; None iff the denominator is 0
```

**`band` means one physical body row (D1/D14).** In `BoundarySupport`, and only
here, a band is a physical body row `r` with `header_rows <= r < n_rows`. Every
count is over absolute grid-row indices; no field is an index into
`logical_row_bands`, and no field is body-relative. `band_count` is the
normative body-row count, `n_rows - header_rows` (this requires
`header_rows <= n_rows`; otherwise `mapping_row_band_not_canonical`), and
`LogicalBoundaryDecision.row_bands` always has that same length. The field name
`band_count` is retained only for compatibility; no implementation or document
may read it as `len(logical_row_bands)`. The projection bands of §5.4 use a
separate full-table index space that includes header bands; the two index
spaces never mix. An empty body row stays in `band_count`; it is excluded only
from an evidence-specific denominator that requires a word.

**`supported_bands`, `nonempty_bands` and `support_ratio` (D1).**
`supported_bands` is the number of distinct body rows in the union of the
rule-row set and the gutter-row set. `nonempty_bands` is the evidence-specific
denominator below and may be a narrower row set. There is no required ordering
between the two: `supported_bands` may be greater than `nonempty_bands`, and
`support_ratio` may therefore exceed 1.0. `support_ratio` is diagnostic: it is
never a probability, never clamped, never NaN or infinite, and never decides a
boundary by itself. It is `None` exactly when `nonempty_bands == 0`; otherwise
it equals `supported_bands / nonempty_bands` and the validator recomputes it
within `1e-9`. Count constraints are per set, not one global bound:

- `nonempty_bands`, `rule_bands`, `gutter_bands`, `crossing_bands`,
  `short_label_bands` and `condition_bands` are each at most `band_count`;
- `supported_bands` is at most `rule_bands + gutter_bands` and at most
  `band_count`;
- for `subrule_promoted`, `short_label_bands` is at most `nonempty_bands`;
- for `subrule_partial`, `condition_bands` is at most `rule_bands`;
- `gutter_bands` is bounded only by `band_count`: a body row may expose a
  gutter while carrying no word, so it counts in `gutter_bands` and not in
  `nonempty_bands`.

**Supporting rows (D8).** The *supporting rows* of a candidate are the physical
body rows that carry at least one of its body evidence kinds at x. A row is
counted at most once, as the union of these three sources:

- a printed rule at x (`rule_bands`);
- a body gutter at x (`gutter_bands`);
- the `structural` source, but only when it is itself keep-worthy: the refs at
  x resolve to at least two distinct `grid_row` values, counted across source
  groups and never twice inside one group (the de-duplication of §5.3 below).
  This is the same repetition threshold as the structural keep row of §6.2.

A row holding several structural refs, or a rule and a gutter and a structural
ref, still contributes exactly one supporting row. Structural refs that do not
reach the two-row repetition threshold contribute zero to `supporting_bands`
and stay diagnostic on the evidence record, so scattered edge refs can never
expand the veto denominator. Header rows and section-like body rows (§5.3.2)
are never supporting rows: they are removed from all three sources before
`supporting_bands` is counted, so `header_canopy` and `table_bbox` evidence
alone yields `supporting_bands == 0`. `supported_bands` remains the diagnostic
union of rule and gutter rows used by `support_ratio` and is not the veto
denominator.

A supporting row is **crossed** when a body data-cell bbox or a body word bbox
strictly straddles x, `bbox[0] < x < bbox[2]`, and its row coverage includes
that row. A row increments `crossing_bands` at most once, no matter how many
body data cells or words cross it. `crossing_bands` counts only supporting
rows, so `crossing_bands <= supporting_bands`; a crossing in a non-supporting,
header or section-like row is recorded on the evidence record but never counted
here and never vetoes. The veto is all-or-nothing over the supporting set: one
crossed row removes that row's support only, and an internal candidate is
`unresolved` only when `supporting_bands > 0` and
`crossing_bands == supporting_bands` (§8.1).

The decision uses the explicit thresholds of §6.2, never `support_ratio`. A row
that has both a rule and a gutter increments `rule_bands` and `gutter_bands`
individually but only once in `supported_bands`. The denominator is:

- `subrule_promoted`: body rows **in `rule_bands`** with at least one word
  center strictly right of x, whether or not a source cell was found;
- `label_aligned`: body rows with at least one word anywhere in the table;
- other kinds: body rows with at least one word anywhere in the table.

Both denominators are restated on the corresponding evidence record, so the
validator never has to infer which one a decision used.

**Selected right-side run (D13).** `short_label_bands` and `condition_bands`
are counted per band from **one** run only: the run §6.3 steps 2–3 select for
that band, namely the words strictly right of x inside the unique source cell,
split on `cell_gap_pt`, reduced to the run with the smallest left edge under
the `run_left - m <= 1e-6` tie rule of §6.3 step 3. A band
with zero source cells selects no run and is neither a short-label nor a
condition band; more than one source cell (`subrule_source_cell_ambiguous`) or
a run tie (`subrule_run_tie`) already makes the candidate `unresolved` before
either count is used. No other right-side run in the band may be inspected
for classification, so a band containing both a selected short label and an
unselected condition-like run counts as a short-label band only. Because one
selected run has exactly one lexical class, a band contributes to at most one
of the two counts. Both counts are zero for every non-subrule candidate,
because no run selection exists for those evidence kinds.

```text
LogicalBoundaryDecision
  candidate_x: float                           # group x
  anchor_x: float                              # fixed anchor of the group
  source_xs: tuple[float, ...]                 # every member x, sorted, unique
  decision: LogicalBoundaryDecisionKind
  reasons: tuple[str, ...]                     # stable machine-readable codes
  sources: tuple[LogicalBoundarySource, ...]
  row_bands: tuple[int, ...]                   # every body grid row, absolute
  boundary: LogicalBoundary | None             # only when decision == "keep"
  demoted_to: "no_evidence" | "condition_path" | None
  support: BoundarySupport
  evidence: tuple[LogicalBoundaryEvidence, ...]  # all evidence seen at x
```

`row_bands` is the ordered tuple of every body grid row,
`header_rows, header_rows + 1, ..., n_rows - 1`. It is not a per-decision
subset, not a projection-band list, and not a body-relative index. Every
decision, including outer, keep, demote and unresolved, carries the same tuple,
so `len(row_bands) == support.band_count` always holds. Narrower evidence sets
live on their own records: `SubrulePromotedEvidence.rule_bands`,
`SubrulePartialEvidence.condition_bands`,
`LabelAlignedEvidence.grid_rows`,
`StructuralEdgeEvidence.physical_cell_edge_refs`. The projection bands of §5.4
use an independent full-table index space; values from the two spaces are never
compared.

`demoted_to` is `None` for `keep` and `unresolved`. It is `"no_evidence"` for
`demote_no_evidence` and `"condition_path"` only for
`demote_condition_path`.

`logical_boundary_decisions` is a diagnostic record. It is retained even when
the table is `unresolved`, but it is never consumed by extraction and never
treated as a logical lattice.

### 5.3 Boundary evidence union (R4, P0-2)

`LogicalBoundaryEvidence` is a discriminated union, not one wide record with
optional fields. Each `kind` has its own required fields, and the validator can
reject a missing or mismatched reference without guessing which field was meant.

```text
PrintedRuleEvidence
  kind: "printed_rule"
  visual_boundary_index: int
  visual_segment_indices: tuple[int, ...]
  coverage: float

SubruleLabelAssignment
  grid_row: int
  physical_cell_ref: PhysicalCellRef
  word_ids: tuple[str, ...]          # non-empty, reading order
  selected_run_bbox: BBox            # union of the assigned word bboxes
  classification: "short_label"

SubrulePromotedEvidence
  kind: "subrule_promoted"
  visual_boundary_index: int
  visual_segment_indices: tuple[int, ...]
  rule_bands: tuple[int, ...]        # absolute body grid rows, sorted, unique
  nonempty_bands: int
  label_assignments: tuple[SubruleLabelAssignment, ...]  # one per band at most
  short_label_ratio: float

SubrulePartialEvidence
  kind: "subrule_partial"
  visual_boundary_index: int
  visual_segment_indices: tuple[int, ...]
  coverage: float
  rule_bands: tuple[int, ...]        # absolute body grid rows
  nonempty_bands: int
  condition_bands: tuple[int, ...]   # subset of rule_bands
  condition_observations: tuple[ConditionObservation, ...]

ConditionObservation
  grid_row: int                      # member of condition_bands
  physical_cell_ref: PhysicalCellRef
  word_ids: tuple[str, ...]          # non-empty, reading order, exactly the selected run
  lexical_class: str                 # one of the §6.3.1 classes
  relational_markers: tuple[str, ...]  # non-empty, ordered, de-duplicated

HeaderCanopyEvidence
  kind: "header_canopy"
  level: int
  boundary_edge: "left" | "right" | "gap"
  left_header_cell_refs: tuple[HeaderCellRef, ...]
  right_header_cell_refs: tuple[HeaderCellRef, ...]
  left_anchor_ref: HeaderCellRef
  right_anchor_ref: HeaderCellRef
  left_label: str
  right_label: str

LabelAlignedEvidence
  kind: "label_aligned"
  grid_rows: tuple[int, ...]
  word_ids: tuple[str, ...]
  gutter_bands: int
  nonempty_bands: int
  gutter_ratio: float

StructuralEdgeEvidence
  kind: "structural"
  physical_cell_edge_refs: tuple[PhysicalCellEdgeRef, ...]  # sorted, unique
  physical_rule_component_ids: tuple[int, ...]

TableBBoxEvidence
  kind: "table_bbox"
  edge: "left" | "right"
  page_number: int
  table_bbox: BBox

RegionExtentEvidence
  kind: "region_extent"
  edge: "left" | "right"
  page_number: int
  region_component_ids: tuple[int, ...]
  extent_left: float
  extent_right: float
  boundary_source: str
  implied_outer_evidence_index: int
  implied_outer_values: tuple[float, ...]
```

**`HeaderCanopyEvidence` is directed (N1).** The record is self-explanatory:
the audit does not re-run the canopy decision.

- `boundary_edge` defines x from the anchors:
  - `left`: x equals `right_anchor_ref.bbox[0]` (within
    `visual_boundary_tol_pt`);
  - `right`: x equals `left_anchor_ref.bbox[2]`;
  - `gap`: x equals
    `(left_anchor_ref.bbox[2] + right_anchor_ref.bbox[0]) / 2`; the gap width
    must be positive and no header cell at that level may intersect the open
    gap.
- `left_anchor_ref` must appear in `left_header_cell_refs` and
  `right_anchor_ref` in `right_header_cell_refs`. Anchors are the cells
  immediately adjacent to x at `level`. Because both lists are nearest-first,
  the anchor is exactly the first element of its list; a record whose anchor is
  not the head of a non-empty list is `boundary_evidence_mismatch`.
- `left_header_cell_refs` lists every header cell at `level` whose x-span lies
  wholly on the left (`bbox[2] <= x + tol`), nearest first; the right list is
  the mirror image (`bbox[0] >= x - tol`, nearest first). Extra refs are
  provenance for a multi-cell canopy, not additional anchors.
- `left_label` / `right_label` are the normalized texts of the anchors
  (strip, collapse internal whitespace); both non-empty and distinct.
- If two cells at the same level touch x within tolerance, the candidate is
  `unresolved` (`header_level_tie`); one anchor per side is mandatory.
- Every ref has `level == evidence.level` and resolves to exactly one
  `DetectedHeaderCell` by `(level, source_row, source_column, column)`; its bbox
  is inside the table bbox.

**`SubrulePromotedEvidence` is per body row, per cell, per word (N2/D14).**

- `rule_bands` is sorted and unique, inside `header_rows .. n_rows - 1`.
- The **source cell** of a body row is the unique `DetectedCell` whose bbox
  contains `x` (`bbox[0] <= x <= bbox[2]`) and whose grid-row coverage includes
  that row. Containment is closed at both endpoints on purpose: when `x` lies
  exactly on an edge shared by two cells, both qualify, the row has no source
  cell, and the candidate is `unresolved` (`subrule_source_cell_ambiguous`).
  This is a deliberate fail-closed boundary, not a rounding artefact. No
  half-open rewrite and no epsilon are permitted, because either would silently
  change physical cell ownership.
- `nonempty_bands` is the number of rows in `rule_bands` with at least one word
  center strictly right of x, counted before classification and regardless of
  whether a source cell was found. It is recomputable and never smaller than
  `len(label_assignments)`. A row with right-side words but an ambiguous source
  cell still counts in the denominator; the denominator is never "rows that
  produced a source cell".
- At most one `SubruleLabelAssignment` per `grid_row`; `grid_row` is unique,
  sorted, and a member of `rule_bands`.
- Each assignment's `physical_cell_ref` resolves to a real `DetectedCell`;
  `word_ids` is non-empty, in reading order, every center strictly right of x
  and inside that cell (same 0.8pt tolerance as `_assign_words`);
  `selected_run_bbox` is exactly the union of those word bboxes.
- The selected run is the nearest word run immediately right of x inside the
  same physical cell and inside that row's y interval. Run splitting is exactly
  §5.3.1: the cell's words sorted by `(x0, word_id)`, split only when the gap is
  strictly greater than `cell_gap_pt`. Let `m` be the smallest left edge among
  that row's right-side runs. The selection is that minimum run; no run is
  chosen by word count, text or list order. A run is tied iff
  `run_left - m <= 1e-6`. The comparison is against `m` only and is never
  chained from one run to the next, so a run farther than `1e-6` from `m`
  cannot tie through an intermediate run. Any tie in any band is
  `subrule_run_tie`, and the whole candidate is unresolved, not only that
  band.
- Only runs classified as `short_label` by §6.3 appear. A row with no
  right-side word is excluded from numerator and denominator.
- `short_label_ratio = len(label_assignments) / nonempty_bands`, with
  `nonempty_bands > 0`. Missing, duplicate or out-of-row assignments are
  errors. The validator recomputes both the count and the ratio.

**`SubrulePartialEvidence` (D2/D14).**

- `rule_bands` is the sorted, unique set of body rows where `rule_at(x, row)`
  is true (§5.3.1).
- `nonempty_bands` is the number of rows in `rule_bands` with at least one word
  center strictly right of x; it uses the same denominator rule as promotion.
- `condition_bands` is the sorted, unique subset of `rule_bands` whose
  right-side selected run is condition-like by §6.5. It must be non-empty for a
  `demote_condition_path` decision.
- There is exactly one `ConditionObservation` per member of `condition_bands`,
  with a unique `grid_row`, sorted by `grid_row`.
- Each observation's `physical_cell_ref` resolves; `word_ids` is non-empty, in
  reading order, every center strictly right of x and inside that cell, and is
  exactly the selected run of that row. `lexical_class` must equal the §6.3.1
  classification of that run, not merely be a legal enum member.
  `relational_markers` is the ordered, de-duplicated list of markers actually
  present in the selected run: first-occurrence order in reading order, exact
  string de-duplication, non-empty; every entry must be findable in the run's
  words. Any disagreement is `condition_path_decision_mismatch`.
- If selected-run resolution produces `subrule_run_tie`, no observation is
  emitted for that row, the row is not added to `condition_bands`, the
  candidate is `unresolved`, and no `ConditionPathRecord` may reference it.
  This is a selection failure, not a `condition_path_decision_mismatch`.
- `coverage` is copied from the matching S2a internal boundary and must equal
  it exactly; S2b never recomputes it.
- Stage A may set `demote_condition_path` only when the decision's `evidence`
  contains exactly one `subrule_partial`. Zero or several members is
  `condition_path_decision_mismatch`.

**`LabelAlignedEvidence` ratio.**

- `grid_rows` is the sorted, unique set of body rows (`header_rows <= r <
  n_rows`) where a gutter exists at x; `gutter_bands = len(grid_rows)`. A word
  crossing x in one of these rows is not an evidence error: it is counted by
  `crossing_bands` and removes that row's support only (§5.3, §8.1). This
  sentence is in conflict with §5.3.1 and is OPEN until §14 item 23 is ruled.
- `nonempty_bands` is the number of body rows with at least one word anywhere
  in the table, recomputed from the fresh parse. An empty body row may carry a
  gutter, so it counts in `gutter_bands` and not in `nonempty_bands`;
  `gutter_ratio` may therefore exceed 1.0, which is diagnostic, not an error.
- `gutter_ratio = gutter_bands / nonempty_bands` with `nonempty_bands > 0`; a
  stored ratio that does not recompute within `1e-9` is
  `boundary_evidence_mismatch`.
- `word_ids` is the reading-order list of words in the gutter rows that do not
  cross x; each id must resolve and lie inside the table.

**`StructuralEdgeEvidence` de-duplication (S3).**

- Refs are sorted by `(grid_row, cell_index, edge)`. That exact triple may
  appear once; a repeat is `boundary_evidence_duplicate_ref` and is rejected.
- Several distinct cells may reference the same `(grid_row, edge)`. They form
  one **source group**: every ref is kept. The group must satisfy
  `max(edge_xs) - min(edge_xs) <= visual_boundary_tol_pt`, i.e. every member is
  measured against the group extremes, never against the previous ref. Chain
  membership is forbidden: refs whose consecutive gaps are all within tolerance
  but whose total span exceeds it are `unresolved`
  (`boundary_evidence_mismatch`). There is no "at most one ref per
  `(grid_row, edge)`" rule; the group is the unit and no ref is collapsed to a
  representative.
- "Repeats in at least two row bands" counts distinct `grid_row` values across
  groups. It never counts cells inside a group, so one row with three agreeing
  cells is still one band.
- Every ref resolves; its edge x is within `visual_boundary_tol_pt` of the
  logical x; `physical_rule_component_ids` is a subset of `region_components`.

**`TableBBoxEvidence` is anchored to a fresh parse (N3).**

- `page_number` and `table_bbox` are copied verbatim from the fresh
  `DetectedTable`; the validator requires exact equality with the fresh parse
  (integer page, float bbox; no per-evidence bbox is allowed).
- `edge` selects `table_bbox[0]` (left) or `table_bbox[2]` (right); x must equal
  that value within `visual_boundary_tol_pt`.
- A page-number or bbox mismatch is `boundary_evidence_stale`, not a warning.
  The evidence may not define its own coordinate system.
- Only outer boundaries may use this kind.

**`RegionExtentEvidence` has a defined encoding (N3).**

The current parser constructs `implied_outer` in
`icpdf.parser.table_regions::_region_from_cluster` with `values = (left, right)` and
`component_ids = tuple(member.component_id for member in members)`; a region
emits at most one such record. The evidence records that encoding instead of
relying on positional convention:

- **Region identity is resolved before anything else.** The region is chosen
  from the table, never from geometry. The fresh parse runs the same
  `detect_table_regions(layout, params)` pass; the target region is the one
  whose component-id set equals `set(DetectedTable.region_components)`
  as recorded by `icpdf.parser.table_detector::detect_tables`. Exactly one
  region must match: zero matches is
  `boundary_evidence_missing_ref`, two or more is `region_lattice_inconsistent`.
  The matched region must also satisfy `region.source ==
  table.detection_method`, `region.boundary_source == table.boundary_source`
  and the same page; any mismatch is `boundary_evidence_stale`. An equal
  extent alone never establishes ownership.
- `implied_outer_evidence_index` is the index into the fresh
  `TableRegion.evidence` tuple where `kind == "implied_outer"`, inside the
  region identified above.
- `implied_outer_values` equals that record's `values` exactly;
  `extent_left == implied_outer_values[0]` and
  `extent_right == implied_outer_values[1]`.
- `region_component_ids` equals that record's `component_ids` as a set, sorted.
- `boundary_source` equals the fresh `TableRegion.boundary_source` and is one
  of `implied_horizontal`, `implied_alignment`, `mixed`.
- `page_number` equals the fresh region page; `edge` selects `extent_left` or
  `extent_right`, and x must equal it within `visual_boundary_tol_pt`.
- If the fresh parse has no `implied_outer` record, the evidence is invalid:
  fail closed with `boundary_evidence_missing_ref`. Never infer the extent from
  the bbox.
- Only outer boundaries may use this kind.

`PhysicalCellEdgeRef`:

```text
grid_row: int
cell_index: int            # index inside DetectedRow.cells
edge: "left" | "right"
```

`HeaderCellRef` is the existing parser tuple
`(level, column, text, bbox, source_row, source_column)`; S2b does not create a
second header extraction.

Source-to-evidence mapping:

| `LogicalBoundarySource` | Required evidence kind(s) |
| --- | --- |
| `printed_rule` | `printed_rule` |
| `subrule_promoted` | `subrule_promoted`, with `nonempty_bands >= 2` and at least one `label_assignments` entry |
| `header_canopy` | `header_canopy`, with both anchors |
| `label_aligned` | `label_aligned` |
| `structural` | at least one of `structural`, `table_bbox`, `region_extent` |

Outer boundaries (`outer_left` / `outer_right`) additionally require
`table_bbox` evidence. When `boundary_source` is `implied_horizontal` or
`implied_alignment`, they also require `region_extent` evidence. A drawn outer
boundary may carry `printed_rule` as well, but `table_bbox` remains the
unconditional locator.

**Minimum evidence fields and rejection rules.** These are the validator rules
in §11, stated with their sources:

| Kind | Required references | Validation / rejection |
| --- | --- | --- |
| `printed_rule` | `visual_boundary_index`, non-empty `visual_segment_indices` | index in range; `abs(visual_boundaries[i] - x) <= visual_boundary_tol_pt`; each segment index in range; each `VisualSegment.component_id` in `region_components`; each `y0 < y1` inside table bbox; `coverage >= visual_full_height_coverage`; role must be `internal` for an internal boundary, `outer_*` for an outer one. Missing/invalid -> `boundary_evidence_missing_ref` or `boundary_evidence_mismatch`. |
| `subrule_promoted` | `visual_boundary_index`, non-empty `rule_bands`, `nonempty_bands > 0`, `label_assignments` | same visual checks; coverage `< visual_full_height_coverage`; `rule_bands` inside grid rows; `grid_row`s unique and inside `rule_bands`; `len(label_assignments) >= logical_subrule_promote_min_bands`; `short_label_ratio` recomputed from the assignments equals the stored value and is `>= logical_subrule_promote_min_ratio`; every word id exists, is right of `x`, and is in its declared physical cell; `selected_run_bbox` is the word union. Missing/duplicate band -> `boundary_evidence_duplicate_ref`; ratio mismatch -> `boundary_evidence_mismatch`; run tie -> `subrule_run_tie`, and a tied band emits no `ConditionObservation`, does not enter `condition_bands`, and makes the whole candidate unresolved. |
| `header_canopy` | `level`, `boundary_edge`, both anchor refs, non-empty left/right ref lists, `left_label`, `right_label` | two ordered resolution steps. Step 1, identity: the key `(level, source_row, source_column, column)` must match exactly one `DetectedHeaderCell`; zero matches -> `boundary_evidence_missing_ref`, more than one -> `header_ref_ambiguous`. Step 2, content: `text` and `bbox` equal the matched cell, `level == evidence.level` and `level < header_rows`, bbox inside the table; failure is `boundary_evidence_mismatch`. The steps never swap. The left refs lie at or left of `x`, the right refs at or right; anchors are the nearest cells on their side and satisfy the `boundary_edge` position rule; labels equal the anchors' normalized text and are distinct. A repeated ref inside one declared list is `boundary_evidence_duplicate_ref`; two same-level cells touching `x` within tolerance is `header_level_tie`; an empty required side is `header_missing_for_canopy`; no evidence record at all is `boundary_evidence_missing_ref`. |
| `label_aligned` | non-empty `grid_rows`, non-empty `word_ids` | rows in `[header_rows, n_rows)`; every word id exists on the page and inside the table; `gutter_ratio` recomputes from `gutter_bands` and `nonempty_bands`; `gutter_ratio >= logical_label_min_band_ratio`; `len(grid_rows) >= logical_label_min_bands`; a crossing word is counted by `crossing_bands` at decision level (§5.3), not as an evidence error. |
| `structural` | non-empty `physical_cell_edge_refs` | each ref resolves to a real `DetectedCell`; refs are sorted and unique per `(grid_row, cell_index, edge)`; several refs for one `(grid_row, edge)` form a source group that keeps every ref and must satisfy `max(edge_xs) - min(edge_xs) <= visual_boundary_tol_pt`; the edge is within tolerance of `x`; at least two distinct `grid_row` values remain across groups; a crossing word is counted by `crossing_bands` at decision level (§5.3), not as an evidence error. `physical_rule_component_ids`, when present, must all be in `region_components`. Duplicate triple -> `boundary_evidence_duplicate_ref`; disagreement inside a group -> `boundary_evidence_mismatch`. |
| `table_bbox` | `edge`, `page_number`, `table_bbox` | only for outer boundaries; `page_number` and `table_bbox` equal the fresh `DetectedTable` exactly; `x` equals `table_bbox[0]` (left) or `table_bbox[2]` (right) within tolerance. Stale page/bbox -> `boundary_evidence_stale`. An internal boundary may not use this kind. |
| `region_extent` | `edge`, `page_number`, non-empty `region_component_ids`, `extent_left`, `extent_right`, `boundary_source`, `implied_outer_evidence_index`, `implied_outer_values` | only for outer boundaries; the region is resolved first by `region_components` equality (zero matches -> `boundary_evidence_missing_ref`, several -> `region_lattice_inconsistent`); `implied_outer_evidence_index` then selects that region's `TableRegion.evidence` record of kind `implied_outer`; `implied_outer_values == values`, `extent_left == values[0]`, `extent_right == values[1]`; `region_component_ids` equals that record's `component_ids` set; `boundary_source` equals the fresh region source and is in `{implied_horizontal, implied_alignment, mixed}`; `x` equals the selected extent within tolerance. Missing record -> `boundary_evidence_missing_ref`; mismatch -> `boundary_evidence_stale`. Never infer an extent from the bbox. |

`visual_segment_indices` are indices into `VisualBoundary.segments` for the
boundary at `visual_boundary_index`. The S2a segment order is deterministic
(`visual_structure.py` sorts by `(x, y0, y1, component_id)`), so the same
parser and parameters reproduce the same indices. This is the only primitive
provenance chain; S2b does not copy `primitive_indices` a second time.

#### 5.3.1 Normative geometric predicates (D3)

These predicates are normative. They restate the existing geometry so an
independent validator can recompute it from `grid.xs`, `grid.ys`,
`layout.words`, `DetectedCell` records and the S2a tuples without calling S1
helpers.

**Preconditions.** Before any predicate, require `n_rows >= 1` and
`len(grid.ys) == n_rows + 1`, with `grid.ys` strictly ascending. If either
fails, the existing grid/mapping validation fails and word row assignment is
not run.

**Word universe.** The universe consists exactly of the words actually
assigned to `grid.cells` by §5.6. A word not assigned to any cell is excluded,
including a word outside the table bbox. Assignment tolerance, if any, is
governed exclusively by §5.6 and is not redefined here. Assigned-word and
`unassigned_words` counts are computable from the retained grid. An
out-of-cell page-word count is computable by the validator only when it can
read a fresh `layout.words`
(`len(layout.words) - assigned - len(grid.unassigned_words)`); it is never
serialized, S2c may not require it, and an unavailable value is reported as
"not available" rather than invalidating the table.

*1. Run predicate.* Sort only the universe words assigned to one
`DetectedCell` by `(x0, word_id)`. Never sort or run-split across cells. For
adjacent words `prev` and `next`, let `gap = next.x0 - prev.x1`. They are in
the same run iff `gap` is at most `cell_gap_pt`; `next` starts a new run iff
`gap` is strictly greater than `cell_gap_pt`. A negative gap is at most the
threshold, so overlapping words stay in one run. No second tolerance and no
rounding are applied. This is the only run definition; it matches the
`crossed` test in `icpdf.parser.structure::_rule_grid` but is not delegated to
it at validation time. The parser helper is not itself the normative
definition.

*2. Word crossing predicate.* A word crosses x iff both conditions hold:
`word.x0` is strictly less than x, and x is strictly less than `word.x1`.
Horizontal extent alone decides. `word.x0 == x` and `word.x1 == x` do not
cross. A zero-width word (`x0 == x1`) never crosses. `crossing_bands` is the
number of body rows containing at least one crossing word; several crossing
words in one row count once, and header rows never count. A word in
`grid.unassigned_words` is excluded from every predicate; its count is reported
separately. Crossing uses no second tolerance and no margin.

Gutter and crossing are evaluated independently. A body row can be a rule row
and a crossing row at the same time. It cannot be a gutter row and a crossing
row at the same time, because the gutter predicate requires that no word
crosses x.

*3. Rule matching predicates.* `rule_at(x, row)` and `row_coverage(x, row)` are
separate quantities.

`rule_at(x, row)` is true iff an S2a internal boundary resolves to x and at
least one of its segments, clipped to the row interval
`[grid.ys[row], grid.ys[row + 1]]`, has positive length. It is an existence
test only; it says nothing about how much of the row is covered.

`row_coverage(x, row)` is the covered proportion:

1. Clip every segment of the matching boundary to the row interval; discard
   non-positive lengths.
2. Sort by start. Merge an interval into the current one when its start is at
   most the current end plus `visual_boundary_tol_pt`. Sum the merged lengths.
3. `row_coverage = min(1.0, merged_length / (grid.ys[row + 1] - grid.ys[row]))`.

The tolerance is the local seam tolerance used by S2a
`icpdf.parser.visual_structure::_union_length`: every gap at most `visual_boundary_tol_pt`
between adjacent segments is absorbed. It is not a global gap budget; several
absorbed seams can accumulate, and `row_coverage` may be 1.0 while the raw
union has small gaps. This is intentional and matches S2a. A row with no
segment has `row_coverage == 0.0` and `rule_at == False`.

Matching boundary x:

- no matching internal boundary means `rule_at` is false;
- exactly one internal boundary within `visual_boundary_tol_pt` of x is
  selected;
- more than one matching internal boundary is `boundary_evidence_mismatch` and
  the candidate is `unresolved`, regardless of whether the distances are
  equal; `rule_at` is then not evaluated;
- x is `boundary.x`; `VisualSegment` has no x field, and per-segment x is not
  re-tested;
- the row interval uses `grid.ys`, whose strict ascent is a precondition.

Evidence thresholds use the S2a overall coverage, not `row_coverage`:

- `printed_rule` requires the matching boundary's S2a `coverage` to be at least
  `visual_full_height_coverage`. There is no per-body-row coverage requirement:
  a boundary may meet the overall threshold while one or more body rows have no
  segment. `printed_rule` classification and `rule_bands` membership are
  independent checks, and `PrintedRuleEvidence` carries no `rule_bands`.
- `subrule_partial` requires that `coverage` be strictly greater than 0 and
  strictly less than `visual_full_height_coverage`.
  `SubrulePartialEvidence.coverage` is exactly that S2a value, copied; it is
  never a row coverage and is never recomputed by S2b.
- `rule_bands` in both `SubrulePromotedEvidence` and
  `SubrulePartialEvidence` is the sorted tuple of body rows where
  `rule_at(x, row)` is true. It records rows with rule evidence, not rows fully
  covered; a partial rule legitimately contributes such rows. An empty
  `rule_bands` means no body-row rule evidence and cannot produce
  `demote_condition_path`; such a candidate falls to `demote_no_evidence`.
- `row_coverage` is recomputed by the validator as a diagnostic. It gates
  neither `printed_rule` nor `subrule_partial`, and it is not stored.

*4. Band (body-row) word assignment predicate.* Only words in the §5.6
universe are assigned. For a word, let `cy = (word.y0 + word.y1) / 2`. Its
physical row `row_of(word)` is the largest `r` in `0 .. n_rows - 1` with
`grid.ys[r]` at most `cy`; if no such `r` exists, the row is 0. Because
`grid.ys` is sorted, the result is unique and is clamped to
`0 .. n_rows - 1`. A word whose center is above the first boundary maps to row
0; a word whose center is on or below the last boundary maps to
`n_rows - 1`.

Every assigned word belongs to exactly one physical row, hence to either the
header rows or one body row. A word is never counted in two rows, and no
assigned word is dropped by this rule. A body row is non-empty iff at least one
assigned word maps to it. This y assignment is independent of
`_assign_words`, which selects a physical cell by the full center point; their
disagreement is not an error, because the cell assignment owns word partitions
and the row assignment owns evidence counting.

#### 5.3.2 Section-like body rows (D16)

S2b does not classify section or label semantics. The section exemption is
therefore purely geometric and reads only persisted physical cells, `grid_ys`
and the table bbox. It never reads cell text, never consults a section
classifier, and never tests `column_span` as the sole criterion.

A body row `r` (`header_rows <= r < n_rows`) is **section-like** iff there
exists a persisted `DetectedCell` `c` such that:

- the row coverage of `c` contains `r`:
  `c.grid_row <= r <= c.grid_row + c.row_span - 1`; and
- the bbox of `c` spans the table horizontally:
  `c.bbox[0] <= grid.bbox[0] + visual_boundary_tol_pt` and
  `c.bbox[2] >= grid.bbox[2] - visual_boundary_tol_pt`.

Header rows (`r < header_rows`) are exempt by that range alone and are never
tested with this predicate. A section-like row is removed from
`rule_bands`, `gutter_bands` and the structural source **before**
`supporting_bands` is counted, so it is neither a supporting row nor a
crossing row; a crossing there is recorded on the evidence record as a
diagnostic only. It remains in `band_count` and in `LogicalBoundaryDecision.row_bands`,
because those describe the body row range, not the evidence set. The same
predicate is used by §5.2, §6.2, §8.1 and §11 invariant 20. When the predicate
is absent or cannot be evaluated, the row is not exempt and the candidate fails
closed through the ordinary supporting-row rules.

### 5.4 Projection models (R3, P1-2, P1-4)

```text
PhysicalColumnOverlap
  band_index: int                      # full-table projection band index
  physical_column: int                 # 0-based interval index into the one grid.xs
  physical_left: float                 # grid.xs[physical_column]
  physical_right: float                # grid.xs[physical_column + 1]
  region_component_ids: tuple[int, ...]  # provenance only; may be empty
  grid_row_start: int                  # copied from the band, inclusive
  grid_row_end: int                    # copied from the band, inclusive
  overlap_left: float
  overlap_right: float
  overlap_fraction: float              # overlap width / physical column width

ColumnProjection
  logical_column: int
  left: float
  right: float
  physical_columns: tuple[PhysicalColumnOverlap, ...]  # coverage, not a partition
  visual_column_indices: tuple[int, ...]                # visual interval indices

BandCellShape
  column: int            # DetectedCell.column_index
  column_span: int
  row_span: int

BandObservation
  band_index: int        # full-table index; includes header bands
  section: "header" | "body"
  grid_row_start: int    # inclusive
  grid_row_end: int      # inclusive
  shape: tuple[BandCellShape, ...]
```

`physical_column` is unique **within one table** because one table has exactly
one `grid.xs` (§3.2). `physical_left` / `physical_right` are copied from that
lattice at derivation time and are the self-checking locator; the validator
re-derives `grid.xs` from a fresh parse and requires
`physical_left == grid.xs[i]` and `physical_right == grid.xs[i + 1]`.
`band_index` is an index into `logical_row_bands`; `grid_row_start` and
`grid_row_end` are that band's closed row interval, copied for locator and
readability only and never an independent row authority. Any disagreement
between the three is `mapping_row_band_not_canonical`.

`region_component_ids` records which components contributed the physical
column. It is provenance, not a lattice selector; there is no
`region_local_column` field because no region-local x lattice exists in the
current repository.

**Table-level projection bands (D1).** The bands are a property of the table,
not of a logical column, and are derived before any projection:

1. For each physical row `r` in `[0, n_rows - 1]`, build the signature `S(r)`:
   the multiset of `BandCellShape(column, column_span, row_span)` over every
   `DetectedCell` whose row coverage contains `r`.
2. Sort each signature ascending by `(column, column_span, row_span)`.
   Duplicates are retained: two cells with the same triple produce two entries.
   Two signatures are equal iff they have the same length and are equal item by
   item in canonical order.
3. Forced split points are row `0`, row `n_rows`, and row `header_rows` when
   `0 < header_rows < n_rows`. A forced split wins: the two rows on either side
   are never merged even when their signatures are equal.
4. Between adjacent forced split points, merge maximal consecutive runs of equal
   signature. A row with no covering cell has the empty signature `()`; empty
   rows merge with empty rows. The empty signature is a normal signature and is
   never dropped. A table with no empty row has no empty band.
5. Emit one `BandObservation` per run in ascending row order: `band_index` is
   its 0-based position, the row interval is closed, and `section` is
   `"header"` iff `grid_row_end < header_rows`, otherwise `"body"`. The forced
   split guarantees that no band straddles `header_rows`.
6. The bands partition `0 .. n_rows - 1` exactly: the first start is 0, the last
   end is `n_rows - 1`, and every next start equals the previous end plus 1.
7. A cell whose row coverage crosses the header/body split appears with the
   same triple in the bands on both sides. It is deliberately not decomposed;
   cell identity is not part of the signature, so two different cells with the
   same triple are indistinguishable here.

`logical_row_bands` is the ordered tuple of all `BandObservation` records. Its
`band_index` is the full-table space and includes header bands. A body-relative
band index is `band_index - header_band_count`, derived only when needed, never
stored, and never compared with an absolute index. §5.2's `BoundarySupport`
uses body **rows**, not these bands; the two spaces never mix.

**Projection over occupied band columns (choice B).**
`PhysicalColumnOverlap` records physical structure coverage, not a purely
geometric interval intersection. A band with an empty shape has no cell
coverage and therefore emits no overlap for any logical column.

Define `occupied_columns(band)` as the set of physical column indices `j` for
which some `BandCellShape` in `band.shape` satisfies
`shape.column <= j <= shape.column + shape.column_span - 1`. `row_span`
participates in the signature but not in this x-occupancy test. A shape whose
`column` is outside `0 .. n_columns - 1`, whose `column_span` is not positive,
or whose covered interval leaves the lattice is
`mapping_row_band_not_canonical`.

For each logical column `[L, R]` and each `BandObservation`:

1. If `band.shape == ()`, emit no `PhysicalColumnOverlap`.
2. Otherwise compute the expected set
   `E = { j in occupied_columns(band) : min(R, grid.xs[j + 1]) - max(L, grid.xs[j]) is positive }`.
3. Emit exactly one record per `j` in `E`, in ascending `physical_column`
   order. An empty `E` emits no record and is not an error.
4. Emit nothing for a `j` outside `E`; an extra record is
   `mapping_row_band_not_canonical`.
5. Sort records by `(band_index, physical_column)`.

`ColumnProjection` is a coverage relation, not a partition of bands. A band may
contribute zero, one or several overlaps to a logical column. Empty bands
contribute zero to every logical column and are still part of
`logical_row_bands`. Adjacent bands may carry the same, different or empty
sets. No rule requires every band to appear in every logical column. "Complete
projection" means every occupied band is examined, not that every physical row
appears in the overlap list.

**Band failure ownership (5.4a / 5.4b / 5.4c).**

- 5.4a `mapping_row_band_not_canonical`: a `band_index` outside
  `0 .. len(logical_row_bands) - 1`; a row field that differs from its band; a
  band signature run that is not maximal; a band order other than ascending
  `(grid_row_start, physical_column)`; a missing or duplicated band; a shape
  outside the lattice; an overlap emitted for an empty band; a duplicate
  `(band_index, physical_column)`; a missing member of `E`; or a
  `physical_column` that repeats or is not ascending within a band.
- 5.4b `mapping_row_band_overlap`: an uncovered row between two existing
  bands. The code name explicitly includes a gap; an implementation must test
  both gap and intersection, and testing only intersection is a defect.
- 5.4c `mapping_row_band_overlap`: two existing band row ranges intersect, or a
  band is fully duplicated.

`mapping_row_band_overlap` is checked once on the table bands, not per logical
column. `mapping_lattice_index_mismatch` does not absorb any of these three
checks.

**Overlap geometry is recomputable.** For a logical interval `[L, R]` and
physical interval `[grid.xs[i], grid.xs[i + 1]]`:

```text
overlap_left  = max(L, grid.xs[i])
overlap_right = min(R, grid.xs[i + 1])
overlap_fraction = (overlap_right - overlap_left)
                   / (grid.xs[i + 1] - grid.xs[i])
```

**Overlap checks are two ordered checks.**

6.1a Range check (construction stage; owns range failures).

- The authoritative overlap width between the logical interval and the
  physical interval must be positive. Zero or negative width is
  `mapping_physical_overlap_missing`; the table is unresolved.
- With positive width, the stored `overlap_fraction` must lie in `(0, 1]`. A
  stored value outside that range is `boundary_evidence_mismatch`; the table is
  unresolved. This is a range failure of the projection payload, not a
  recompute-consistency failure.
- 6.1a runs before 6.1b for each projection record. A record that fails 6.1a is
  not passed to 6.1b, so one record produces one code.

6.1b Recompute-consistency check (validation stage; namespace A).

- For a record that passes 6.1a, recompute `overlap_left`, `overlap_right` and
  `overlap_fraction` from the authoritative logical interval and the physical
  width.
- Any absolute difference greater than `1e-6` is an artifact-integrity hard
  error: namespace A, validator failure, no B code, and never added to
  `logical_mapping_reason`.
- 6.1b does not re-emit `mapping_physical_overlap_missing` or
  `boundary_evidence_mismatch` for the same record; 6.1a already owns the range
  failures.

**Visual intervals are reconstructed, not guessed (S2).**

When `visual_columns is not None`, `visual_boundaries` is sorted and

```text
len(visual_boundaries) == visual_columns + 1
visual interval i = [v[i], v[i + 1]]   for every 0 <= i < visual_columns
```

Membership is decided by positive width, never by point placement, so the
endpoint convention cannot change the index set:

```text
logical interval [L, R] overlaps visual interval i iff
min(R, v[i + 1]) - max(L, v[i]) > 0
```

Touching at a single x (zero width) is not an overlap, so the half-open/closed
convention only removes ambiguity for a point and cannot change the index set.
`visual_column_indices` is the sorted, unique list of intervals with positive
overlap. It is empty when `visual_columns is None`. A length mismatch between
`visual_boundaries` and `visual_columns` is
`mapping_visual_interval_mismatch`.

`ColumnProjection` is the **only authoritative** projection payload. It lives
once on the table in `column_projection`, ordered by `logical_column`. A
proposed `LogicalColumn` does not embed a copy. The validator enforces
one-to-one order, `column_projection[i].logical_column == i`, and
`column_projection[i].left == logical_boundaries[i]`,
`column_projection[i].right == logical_boundaries[i + 1]` for a resolved table.

### 5.5 `LogicalColumn` and role provenance (P1-3)

```text
LogicalColumn
  logical_column: int
  header_path: tuple[str, ...]          # top-to-bottom, may be empty
  header_cell_refs: tuple[HeaderCellRef, ...]
  role: ColumnRole                      # existing vocabulary; "unknown" allowed
  role_source: "header_text" | "subrule_short_label"
             | "heuristic" | "fail_closed"
  role_evidence: str | None             # stable code, not prose
  role_header_cell_ref: HeaderCellRef | None   # parser level
  role_header_cell_id: str | None              # domain level
```

This aligns with the existing `Candidate` fields (§3.4) instead of inventing a
`header | unknown` vocabulary:

- header-derived role: `role_source = "header_text"`,
  `role_header_cell_ref` / `role_header_cell_id` populated;
- promoted sub-rule column — the logical column immediately to the right of a
  kept `subrule_promoted` boundary: `role = condition`,
  `role_source = "subrule_short_label"` (the approved S2 value),
  `role_evidence = "repeated_short_label"`, header reference `None`;
- unlabelled column: `role = unknown`, `role_source = "fail_closed"`,
  `role_evidence = None`, no header reference;
- any other documented layout rule: `role_source = "heuristic"` with a stable
  `role_evidence` code naming the rule.

**Role recipient (D9).** A promoted boundary at x assigns the role to exactly
one record: the logical column whose left boundary is x, that is
`[x, logical_boundaries[i + 1])`. The column to the left of x does not receive
it, and a physical cell straddling x is not a recipient. Because a logical
column has exactly one left boundary, it can receive at most one
`subrule_short_label` role; two promoted boundaries in one physical cell make
the middle column the recipient of the left boundary and the right column the
recipient of the right boundary. Promotion is internal-only, so a recipient
column always has positive width.

The recipient's `header_path` and `header_cell_refs` are preserved, but
`role_source = "subrule_short_label"` takes precedence over `header_text` and
`heuristic` for `role` / `role_evidence`, and both `role_header_cell_ref` and
`role_header_cell_id` are `None` per the matrix below. A `demote_*` or
`unresolved` candidate confers no role, even when its short labels matched.

`role_source` is the existing free-form `str` on
`icpdf.domain.candidate::Candidate`; `icpdf.parser.candidate_registry` currently
emits `header_text`, `heuristic` and `fail_closed`. The approved S2 design already
reserves `subrule_short_label` for a promoted sub-rule column, so S2b adopts it
as the fourth documented value rather than hiding it in a separate vocabulary.
`section_band` is not used in S2b; it belongs to S2c.

`role_header_cell_ref` and `role_header_cell_id` are two forms of the same
link, not alternatives. They may coexist; there is no "at most one" rule. The
validator enforces this matrix per record:

| `role_source` | `role_header_cell_ref` | `role_header_cell_id` | Additional rule |
| --- | --- | --- | --- |
| `header_text` | required at parser level | required after rebuild | both, when present, resolve to the same header cell |
| `subrule_short_label` | must be null | must be null | `role == condition`; record is the right-hand column of a kept promoted boundary |
| `heuristic` | optional | optional | if present, must resolve; no header claim |
| `fail_closed` | must be null | must be null | `role == unknown` |

At parser level the domain id does not exist yet, so only the ref is required;
after rebuild the id is required and the ref is still carried. Both-null is
valid only for `subrule_short_label`, `fail_closed`, and `heuristic`;
`header_text` with both null is `header_role_source_invalid`. A ref/id pair
that resolves to different cells is `boundary_evidence_mismatch`.
`role_evidence` is a stable code, not free prose.

### 5.6 Logical cells and word assignments (R7, P1-1)

```text
PhysicalCellRef
  grid_row: int          # DetectedRow.grid_row
  cell_index: int        # index inside DetectedRow.cells
  column_index: int      # DetectedCell.column_index, for readability
  cell_id: str | None    # domain id after rebuild; None at parser level

PhysicalCellAssignment
  ref: PhysicalCellRef
  word_ids: tuple[str, ...]   # subset of this physical cell's words

LogicalCell
  logical_cell_id: str                 # deterministic, content-independent
  row_start: int                       # inclusive physical grid row
  row_end: int                         # inclusive
  logical_column: int
  logical_column_span: int             # >= 1
  bbox: BBox
  text: str
  kind: "header" | "data"              # section/condition deferred to S2c
  physical_cells: tuple[PhysicalCellAssignment, ...]  # non-empty
  word_ids: tuple[str, ...]            # derived union; disjoint across cells
```

`PhysicalCellAssignment` is the missing piece in the previous design. A
physical cell is not owned wholesale by one logical cell: when a physical cell
straddles a promoted boundary, the same `PhysicalCellRef` appears in several
assignments, each with a disjoint word subset. `LogicalCell.text` is the
reading-order concatenation of its assigned words, not a copy of the physical
cell's full text. `LogicalCell.word_ids` is the union of its assignments; the
union across all logical cells is a disjoint partition.

`PhysicalCellRef.cell_index` is the parser-level identity because
`DetectedCell` has no `cell_id` (§3.1). After rebuild, `cell_id` is filled and
the domain `Cell` can use `cell_id` directly. `cell_index` is the row-local
index in `DetectedRow.cells`, not the physical grid column and not the flat
`TableGrid.cells` index; `column_index` is carried for readability and must
match the referenced cell.

**Two index spaces (D5).** The flat `TableGrid.cells` index and the row-local
`DetectedRow.cells` index are different:

- the flat index enumerates every `GridCell`, including empty ones, across all
  rows, in `icpdf.parser.structure::_assign_words` order;
- the row-local index enumerates only cells with
  `cell.row == grid_row` and non-empty text, in flat order, in
  `icpdf.parser.table_detector::detect_tables`.

The conversion from a row-local position `j` in row `r` back to a flat index
is therefore

```text
flat = offset(r) + j + skipped_before(r, j)
```

where `offset(r)` counts every flat cell with `cell.row < r` and
`skipped_before(r, j)` counts the empty same-row cells that precede the
target. Counting only preceding non-empty cells is **not** the flat index
whenever the row has an empty cell before the target or any earlier row has
cells. The current pipeline never performs this conversion: `word_ids` are
attached at enumeration time from the flat key, and no flat index is
persisted on `DetectedCell`.

The capture itself is additive. `icpdf.parser.structure::_assign_words`
already builds `by_cell` keyed by the flat index and now stores it as
`icpdf.parser.structure::TableGrid.cell_words`; values keep the `_assign_words`
traversal order, which is `layout.words` order, not reading order.
`icpdf.parser.structure::_alignment_grid` never calls `_assign_words`; it
records each group as `cell_words[len(cells)] = tuple(group)` immediately
before appending the cell, so both grid builders fill the cache.
`icpdf.parser.table_detector::detect_tables` reads
`grid.cell_words.get(flat_index, ())` while it enumerates `grid.cells` and
copies the ids to `DetectedCell.word_ids`;
`icpdf.parser.table_rebuilder::build_table` copies them again to the domain
`Cell.word_ids`. No other consumer may treat this
cache as evidence, and an empty tuple means "this grid builder recorded no
words for that cell", never "the words were disproved".

**Persistence limitation (D5).** `detect_tables` emits a `DetectedCell` only
when `cell.text.strip()` is non-empty in
`icpdf.parser.table_detector::detect_tables`. A grid
cell that carries words but renders empty stripped text is therefore **not**
persisted, even though its ids remain in `TableGrid.cell_words`. No consumer
may read the absence of a `DetectedCell` (or of a `PhysicalCellRef`) as proof
that the cell has no words; the later mapping stage must fail closed instead
of inventing an empty cell. The words remain in the §5.6 universe (they are
assigned to `grid.cells`), so the table is unresolved with
`mapping_word_not_assigned` (§10.2 code 18, §11.0 row 10.5a); an empty cell is
never invented and the words are never silently dropped. The capture is
complete on the grid; the artifact is intentionally narrower.

The physical→logical cell relation is many-to-many and lives on the logical
side. A reverse cache `logical_cell_ids` on `DetectedCell` is derived, never
authoritative.

**Assignment identity (D12).** A `PhysicalCellAssignment` is a nested record,
not a standalone row. Its owner is the containing `LogicalCell`; its identity is
the pair `(logical_cell_id, ref)`, where `logical_cell_id` is the containing
cell's field and `ref` is its `PhysicalCellRef`.

- An assignment instance belongs to exactly one `logical_cell_id`: the logical
  cell whose `physical_cells` tuple contains it. It is never shared by two
  `LogicalCell` records, and no second owner field is stored on the assignment.
- Within one `LogicalCell`, `(logical_cell_id, ref)` is unique; the same
  `PhysicalCellRef` does not appear twice in that cell's tuple.
- Across different `LogicalCell` records, the same `PhysicalCellRef` may appear
  in several assignment instances. Each instance has its own `logical_cell_id`
  and its own `word_ids` subset; those subsets are disjoint per this section.
- `logical_cell_id` is not duplicated as a field on `PhysicalCellAssignment`.
  The nesting is the single source of ownership; a duplicated field would be a
  second source of truth.

```text
PhysicalCellAssignment
  ref: PhysicalCellRef
  word_ids: tuple[str, ...]   # subset of this physical cell's words
  # owner is the containing LogicalCell; no duplicated logical_cell_id field
```

**LogicalCell reconstruction contract (N6).** The following rules are
normative; an independent reader must be able to rebuild each field.

*1. Rowspan, colspan and cell decomposition.*

- One `DetectedCell` covers rows `grid_row .. grid_row + row_span - 1` and
  physical columns `column_index .. column_index + column_span - 1`.
- Assign each of its words to exactly one logical column by center x (§7.3).
  A physical cell whose words land in no logical column produces no
  `LogicalCell`; the rule is about the cell, not about a word that lacks an
  assignment.
- Take the maximal consecutive runs of logical columns that contain at least
  one assigned word. Each run yields one logical-cell candidate:
  `logical_column` = run start, `logical_column_span` = run length, and
  `word_ids` = the cell's words in those columns.
- Candidates from different physical cells with the same
  `(row_start, row_end, logical_column, logical_column_span)` are merged into
  one `LogicalCell`; `physical_cells` lists one `PhysicalCellAssignment` per
  source cell. This is the only merge. Adjacent rows are never merged, and
  cells with different row coverage are never merged.
- `row_start = grid_row`, `row_end = grid_row + row_span - 1`; the range is
  contiguous by construction.
- `logical_column_span` counts the columns that actually carry assigned words;
  it is not `DetectedCell.column_span`. The physical span remains on the
  detected cell.
- Within one logical column, logical-cell row ranges must be disjoint. An
  intersection is `mapping_row_overlap` and the table is unresolved.
- `kind` follows `header_rows`, the number of header rows; physical rows are
  0-based, so the header occupies rows 0 through `header_rows - 1` inclusive.
  `kind = "header"` iff `row_end ≤ header_rows - 1`. `kind = "data"` iff
  `row_start ≥ header_rows`. Any other combination crosses the header
  boundary and is `logical_cell_kind_boundary`, with the table unresolved.
  The two conditions are exhaustive over integer rows: the first accepts every
  cell entirely inside the header, the second every cell entirely inside the
  body, and nothing is left but a crossing cell.

  | `header_rows` | `row_start` | `row_end` | Result |
  | --- | --- | --- | --- |
  | 2 | 0 | 0 | `header` |
  | 2 | 0 | 1 | `header` |
  | 2 | 1 | 1 | `header` |
  | 2 | 2 | 2 | `data` |
  | 2 | 1 | 2 | `logical_cell_kind_boundary`, unresolved |
  | 0 | 0 | 0 | `data` |

*2. bbox.*

`LogicalCell.bbox` is the union of the bboxes of its assigned words (content
extent). It is not the physical cell bbox, not the intersection with the
logical column, and not a synthetic column rectangle. A word whose bbox
slightly crosses the logical interval is still included because attribution is
by word center. The validator recomputes the union from `word_ids`.

*3. text and word order.*

`LogicalCell.text` is exactly
`icpdf.parser.structure::_words_to_text(assigned_words)`, applied to the
assigned words of the logical cell.
The function is normative; an independent reimplementation must match it
operation for operation:

```text
def words_to_text(words):
    ordered = stable_sort(words, key=lambda w: ((w.y0 + w.y1) / 2, w.x0))
    heights = [w.y1 - w.y0 for w in ordered if w.y1 > w.y0]
    line_tol = max(2.0, (median(heights) if heights else 8.0) * 0.55)
    lines, centers = [], []
    for w in ordered:
        c = (w.y0 + w.y1) / 2
        if lines and abs(c - centers[-1]) <= line_tol:
            lines[-1].append(w)
            centers[-1] = sum((u.y0 + u.y1) / 2 for u in lines[-1]) / len(lines[-1])
        else:
            lines.append([w])
            centers.append(c)
    rendered = [" ".join(w.text for w in stable_sort(line, key=lambda w: w.x0))
                for line in lines]
    return "\n".join(rendered).strip()
```

This block is reproduced byte-exactly in the delivery message, with its
SHA-256, so it can be rebuilt even if a transport swallows `*` or an operator.

Normative details:

- `stable_sort` is stable: equal keys keep the incoming order. `heights`
  excludes every word with `y1 - y0 <= 0`. `median` is `statistics.median`,
  which averages the two middle values for an even count; `8.0` applies only
  when the filtered `heights` list is empty.
- The line test compares the word center with the running mean of the
  **current last line as it stood before this word was appended**. The mean is
  then recomputed as the arithmetic mean of all word centers in the extended
  line, in line order, using ordinary float addition — never an incremental
  average and never a different summation order.
- A new line's center is exactly that word's own center.
- The within-line sort key is `x0` alone, not `(x0, word_id)`; ties keep the
  line's insertion order. Words are joined by one ASCII space and lines by
  `\n`; the single `.strip()` applies to the whole result, not per line.
- An empty word list returns `""`. Duplicate entries are rendered once each
  and are never de-duplicated here; a duplicated `word_id` is a partition
  error (§5.6 item 5), not something this function repairs.
- The input order is the stored assignment order. The parser builds it in
  `icpdf.parser.structure::_assign_words` by appending in `layout.words` order,
  so a re-render
  from `word_ids` must resolve the ids and pass them in that same order;
  otherwise words with equal `(center, x0)` keys could render differently.

`word_ids` and each assignment's `word_ids` are stored in this reading order.
A split cell's text is therefore a re-rendering of its word subset, never a
prefix or slice of the physical cell's text.

*4. logical_cell_id.*

`table_id` is the domain id built by `build_table`:
`f"p{page_number:03d}-t{table_index:02d}"` in
`icpdf.parser.table_rebuilder::build_table`, where
`table_index` is the 1-based ordinal of the table on its page. The id is:

```text
logical_cell_id = f"{table_id}-lc-{kind}-r{row_start:02d}-r{row_end:02d}"
                  f"-c{logical_column:02d}-s{logical_column_span:02d}"
```

It contains no text, word content, metric, or traversal counter. The S2b
derivation receives the same `(page_number, table_index)` pair that is later
passed to `build_table`; the rebuild must reproduce the same ids. Duplicate ids
within a table are `logical_cell_id_collision`.

*5. Word universe.*

The authoritative universe is the set of words assigned to `grid.cells`,
excluding `grid.unassigned_words`:

- a word is assigned to the first cell in `grid.cells` enumeration order whose
  bbox contains its center with the existing 0.8pt inclusive tolerance in
  `icpdf.parser.structure::_assign_words`;
- a word inside the table bbox but in no cell goes to `unassigned_words` and is
  excluded from the partition; its count is reported, not silently dropped;
- S2b-Schema may extend `_assign_words` to return
  `cell_index -> tuple[word_id, ...]` in the same pass, but must not change its
  iteration order, tolerance or cell fields;
- an independent audit recomputes the universe from a fresh parse with the same
  page, `layout.words` order, center formula and first-match rule. The union of
  all logical assignments must equal it; a missing word is
  `mapping_word_not_assigned`, an extra or duplicated word is
  `mapping_word_partition_mismatch`.

### 5.7 Additive table fields

`DetectedTable` / domain `Table` gain:

```text
logical_mapping_status: LogicalMappingStatus = "unresolved"
logical_mapping_reason: tuple[str, ...] = ()
logical_boundaries: tuple[float, ...] = ()               # accepted x positions
logical_boundary_detail: tuple[LogicalBoundary, ...] = ()  # parallel evidence
logical_columns: int | None = None
column_projection: tuple[ColumnProjection, ...] = ()
logical_columns_detail: tuple[LogicalColumn, ...] = ()
logical_cells: tuple[LogicalCell, ...] = ()
logical_row_bands: tuple[BandObservation, ...] = ()      # projection partition
logical_condition_paths: tuple[ConditionPathRecord, ...] = ()  # S2c input
logical_boundary_decisions: tuple[LogicalBoundaryDecision, ...] = ()  # diagnostic
grid_ys: tuple[float, ...] = ()                          # D6; grid.ys copied verbatim
n_rows: int = 0                                          # D6; grid.n_rows
```

`logical_boundaries` and `logical_boundary_detail` are ordered identically:
`logical_boundaries[i] == logical_boundary_detail[i].x`. The simple x tuple is
the approved umbrella interface; the detail tuple carries evidence. The
validator enforces the parallel order and rejects a length mismatch.

`logical_row_bands` is derived only from `grid.ys`, `n_rows`, `header_rows` and
the `DetectedCell` shape triples. It is populated whenever the table has a grid,
including unresolved tables; on an unresolved table it is diagnostic data,
never a logical lattice, and never consumed by extraction. A resolved table
with an empty tuple is `mapping_row_band_not_canonical`.

`logical_condition_paths` is populated only on a resolved table. It is the only
condition-path list S2c may read; a `demote_condition_path` decision inside
`logical_boundary_decisions` is diagnostic and not a second source. An
unresolved table has an empty tuple (§6.5, §10.1).

`logical_row_bands` and `logical_boundary_decisions` are the diagnostic payloads
retained on an unresolved table; every accepted logical payload stays empty
(§10).

`logical_boundary_decisions` is the only diagnostic payload retained on an
`unresolved` table; all accepted logical payloads stay empty (§10).

`grid_ys` and `n_rows` are physical structure, not logical payload: they stay
populated on an `unresolved` table and are never recomputed from `rows`.
`grid_ys` is `tuple(grid.ys)` as stored by the builder: at least two
coordinates, all finite, strictly ascending, with
`len(grid_ys) == n_rows + 1` and `n_rows >= 1` whenever the lattice is
non-empty. The parser `DetectedTable` and the domain `Table` call the same
`validate_grid_ys` helper, so neither model can be loaded with a
single-coordinate or non-finite lattice. An old artifact with no `grid_ys`
loads with the legacy defaults `()` and `0` (invariant 16).

`DetectedCell` / domain `Cell` gain only derived caches:

```text
logical_cell_ids: tuple[str, ...] = ()
logical_columns: tuple[int, ...] = ()
word_ids: tuple[str, ...] = ()
```

Candidate identity is unchanged. Candidates may gain `logical_cell_refs` and
derived `logical_columns`; when the mapping is unresolved these are empty.

### 5.8 Parameters and snapshot compatibility (R6, P0-4)

All new thresholds are `TableParams` fields with **code defaults**, not YAML
entries. `configs/parser.yaml` is unchanged, so `parser_config_sha256` (the YAML
file hash) is unchanged for old and new runs. Proposed defaults, subject to
Reviewer approval:

| Parameter | Proposed default | Purpose |
| --- | --- | --- |
| `logical_label_min_band_ratio` | 0.60 | stable body-gutter support |
| `logical_label_min_bands` | 2 | minimum gutter row bands |
| `logical_subrule_promote_min_ratio` | 0.50 | short-label promotion |
| `logical_subrule_promote_min_bands` | 2 | minimum short-label bands |
| `logical_subrule_ambiguous_min_ratio` | 0.25 | lower bound of the ambiguous band |
| `logical_short_label_max_words` | 2 | short-label classification |
| `logical_short_label_max_chars` | 12 | short-label classification |

Boundary alignment uses the existing `visual_boundary_tol_pt` (2.5pt); no new
geometry tolerance is introduced.

**Current v1 snapshot.**
`icpdf.parser.config::TABLE_PARAMS_SNAPSHOT_VERSION` names the snapshot version
constant. The v1 snapshot is
`{"snapshot_version": "table-params/v1", "params": params.model_dump(mode="json")}`
as produced by `icpdf.parser.config::table_params_snapshot`, and
`icpdf.parser.config::snapshot_sha256` hashes canonical JSON with sorted
keys. The frozen v1 SHA is
`82d4df4d1cb3cac9741831b0db36e19fa80c1829abc18b3f8b1ab4ee1c6b9f0a`
(`docs/S2A_FREEZE.md`).

The v1 field set is exactly the 20 fields in
`icpdf.parser.config::V1_FIELDS`:

```text
cell_gap_pt, row_gap_factor, column_tolerance, header_min_hits,
max_title_chars, max_cell_chars, min_numeric_cells, rule_min_width_pt,
rule_min_height_pt, alignment_min_rows, merge_min_gap_pt, merge_max_gap_pt,
merge_column_tol_pt, merge_min_shared_columns, merge_shared_ratio,
merge_extent_tol_pt, merge_min_x_overlap_ratio, visual_min_rule_span_pt,
visual_boundary_tol_pt, visual_full_height_coverage
```

**Field names verified (R10-N8FIELDS).** The r9 delivery showed
`merge_column_tol_ptl` inside the decoded §5.8 excerpt. The string is not in
the repository: `icpdf.parser.config::TableParams.merge_column_tol_pt` is
declared, the frozen v1
snapshot in `docs/S2A_FREEZE.md` hashes a `params` object containing
`merge_column_tol_pt`, and the 20-name block above carries that name and no
other spelling of it. The defect
was in the delivered message, whose base64 was retyped instead of copied;
§16.6 records it. The 20 names below are copied from
`icpdf.parser.config::V1_FIELDS` in declaration order, together with the
Pydantic bound and the code default of
each field. This table is the field-set authority, not the prose above it.

| Field | Declared | Accepted JSON | Bound | Default |
| --- | --- | --- | --- | --- |
| `cell_gap_pt` | float | number | `gt 0` | 8.0 |
| `row_gap_factor` | float | number | `gt 0` | 2.5 |
| `column_tolerance` | int | integer | `ge 0` | 2 |
| `header_min_hits` | int | integer | `ge 1` | 2 |
| `max_title_chars` | int | integer | `ge 1` | 120 |
| `max_cell_chars` | int | integer | `ge 1` | 80 |
| `min_numeric_cells` | int | integer | `ge 0` | 2 |
| `rule_min_width_pt` | float | number | `gt 0` | 70.0 |
| `rule_min_height_pt` | float | number | `gt 0` | 15.0 |
| `alignment_min_rows` | int | integer | `ge 2` | 3 |
| `merge_min_gap_pt` | float | number | `ge 0` | 2.0 |
| `merge_max_gap_pt` | float | number | `gt 0` | 24.0 |
| `merge_column_tol_pt` | float | number | `gt 0` | 2.5 |
| `merge_min_shared_columns` | int | integer | `ge 1` | 2 |
| `merge_shared_ratio` | float | number | `gt 0`, `le 1` | 0.6 |
| `merge_extent_tol_pt` | float | number | `ge 0` | 3.0 |
| `merge_min_x_overlap_ratio` | float | number | `gt 0`, `le 1` | 0.6 |
| `visual_min_rule_span_pt` | float | number | `gt 0` | 4.0 |
| `visual_boundary_tol_pt` | float | number | `gt 0` | 2.5 |
| `visual_full_height_coverage` | float | number | `gt 0`, `le 1` | 0.85 |

**Per-field JSON type rules (R10-N8FIELDS).** These run on the stored JSON,
before any `TableParams(**params)` construction:

1. A declared `int` field accepts only a JSON integer. `true` and `false` are
   rejected even though Python's `bool` is a subclass of `int`; the test is
   `type(value) is int`, never `isinstance(value, int)`.
2. A declared `float` field accepts a JSON integer or a JSON float. Integer and
   float JSON types are validated without coercing the stored parsed value. A
   stored `8` stays the integer 8 in the parsed document and a stored `8.0`
   stays the float; neither is rewritten before the canonical hash. Bounds are
   compared numerically, so `8` and `8.0` are equally valid for a float field,
   but they are distinct documents with distinct canonical JSON.
3. `null`, strings, arrays and objects are rejected for both declared types.
4. A non-finite value is rejected; canonical JSON cannot represent `NaN` or
   `Infinity`, and the writer must call `json.dumps(..., allow_nan=False)`.
5. The bound in the table is re-checked on the stored value, so a snapshot that
   satisfies the type rule but violates `gt 0`, `ge 0` or `le 1` is
   `table_params_snapshot_schema_invalid`.

**Hash semantics (R11-N8LOAD-2).** The canonical snapshot hash is SHA-256 over
the canonical JSON serialization of the stored snapshot object, with sorted
keys and no insignificant whitespace, computed by the unchanged
`icpdf.parser.config::snapshot_sha256`. It is not a hash of the original raw
byte sequence. Whitespace, key order and JSON number spelling in the artifact
file therefore do not by themselves change the hash; only the parsed document
does. The validator hashes `document` exactly as the loader parsed it, without a
`TableParams` round-trip and without an int-to-float rewrite, so the frozen v1
SHA `82d4df4d...` is reproduced as before. Switching this document to
raw-byte hashing would break every existing v1 artifact and is not proposed.
`TableParams(**params)` is constructed only after the hash comparison, and its
dump is never hashed.

**Version-dispatched serialization.** S2b must not change what a v1 snapshot
means. Proposed API:

```text
TABLE_PARAMS_SNAPSHOT_VERSION = "table-params/v2"
SUPPORTED_TABLE_PARAMS_SNAPSHOT_VERSIONS = ("table-params/v1", "table-params/v2")
V1_FIELDS = (the 20 names in the field table)
V2_FIELDS = V1_FIELDS + (the seven logical_ names)

class UnsupportedTableParamsSnapshotVersion(ValueError)

_table_params_fields(version) returns tuple of str
    if version == "table-params/v1":
        return V1_FIELDS
    if version == "table-params/v2":
        return V2_FIELDS
    raise UnsupportedTableParamsSnapshotVersion(version)

table_params_snapshot(params, version=TABLE_PARAMS_SNAPSHOT_VERSION) returns dict
    fields = _table_params_fields(version)      # raises; there is no fallback
    dump = params.model_dump(mode="json")
    return {"snapshot_version": version,
            "params": {name: dump[name] for name in fields}}

table_params_sha256(params, version=TABLE_PARAMS_SNAPSHOT_VERSION) returns str
    return snapshot_sha256(table_params_snapshot(params, version=version))
```

`version` is keyword-only in both entry points. There is no `else` branch. The
r9 review correctly observed that
`fields = V1_FIELDS if version == "table-params/v1" else V2_FIELDS` would label
any unknown version as v2 while keeping its caller-supplied version string,
producing a snapshot whose `snapshot_version` and field set disagree.
`table_params_sha256` routes through `table_params_snapshot`, so it inherits the
same refusal and cannot hash an unknown version.

`snapshot_sha256()` itself is unchanged. It hashes the stored snapshot object,
not a freshly dumped model, so replaying an old artifact is stable without
knowing the current field set. The producer
(`icpdf.parser.pipeline::_sanitized_config` and the manifest written by
`icpdf.parser.pipeline::parse_pdf`) passes the current version explicitly;
consumers (`tools.audit_visual_primitives::verify_identity`,
`tools.validate_evidence::validate_run`) hash the stored snapshot and never
re-dump the model.

**Strict snapshot validation (N8, R11-N8LOAD-1).** A computable SHA does not
make a snapshot legal. The validator takes raw bytes and calls the loader
itself, so a caller cannot supply a hand-built document that skipped duplicate
key detection:

```text
class DuplicateTableParamsSnapshotKey(ValueError)

class TableParamsSnapshotParseError(ValueError)

class LoadedTableParamsSnapshot
    raw: bytes       # the exact bytes that were decoded
    document: dict   # {"snapshot_version": str, "params": dict}

_reject_duplicate_keys(pairs) returns dict
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise DuplicateTableParamsSnapshotKey(key)
        seen.add(key)
    return dict(pairs)

load_table_params_snapshot(raw: bytes) returns LoadedTableParamsSnapshot
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TableParamsSnapshotParseError(str(exc))
    try:
        document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise TableParamsSnapshotParseError(str(exc))
    return LoadedTableParamsSnapshot(raw=raw, document=document)

validate_table_params_snapshot(raw: bytes,
                               expected_version: str,
                               expected_sha256: str) returns list of str
    try:
        doc = load_table_params_snapshot(raw)
    except DuplicateTableParamsSnapshotKey:
        return ["table_params_snapshot_duplicate_key"]
    except TableParamsSnapshotParseError:
        return ["table_params_snapshot_parse_error"]
    document = doc.document
    if type(document) is not dict:
        return ["table_params_snapshot_schema_invalid"]
    if set(document) != {"snapshot_version", "params"}:
        return ["table_params_snapshot_schema_invalid"]
    if type(document["params"]) is not dict:
        return ["table_params_snapshot_schema_invalid"]
    # version, per-field type and bound checks, then hash comparison follow
```

`expected_version` and `expected_sha256` are keyword-only. The validator is the
only public validation entry point, and its only input is raw bytes. It has no
parameter that accepts a `dict` or a pre-loaded `LoadedTableParamsSnapshot`, so
a hand-built document cannot be validated and a duplicate key cannot be
collapsed before the check. `load_table_params_snapshot` may be imported for
diagnostics, but its return value is not an approval token: a caller that needs
validation passes the same bytes to the validator, which loads them again.
There is no `table_params_snapshot_untrusted_source` code, because no entry
point can receive an untrusted object any more.

Every consumer reads the artifact bytes and calls the validator. A
`json.loads(...)` call followed by a separate check remains forbidden: once a
plain `dict` exists, a duplicate key has already been collapsed by the parser
and no validator downstream can detect it. The duplicate-key exception is
raised inside `json.loads` by the object hook; it is not a `JSONDecodeError`, so
the loader's parse-error wrapper does not catch it and it reaches the
validator's first `except` branch unchanged.

The read path rejects, in order:

1. a UTF-8 decode failure, empty input or a JSON syntax error:
   `table_params_snapshot_parse_error`;
2. a duplicate JSON object key at any depth, as raised by the
   `object_pairs_hook`: `table_params_snapshot_duplicate_key` with the
   offending key name;
3. a root value that is not a JSON object — an array, string, number or `null`
   parses successfully but is not a snapshot: `table_params_snapshot_schema_invalid`;
4. top-level keys not exactly `{"snapshot_version", "params"}`:
   `table_params_snapshot_schema_invalid`;
5. a `snapshot_version` outside `SUPPORTED_TABLE_PARAMS_SNAPSHOT_VERSIONS`
   (`unsupported_table_params_snapshot_version`), or a supported version that
   differs from `expected_version` read from the manifest or `run_config`
   (`table_params_snapshot_version_mismatch`);
6. `params` that is not a JSON object — including an array, string, number or
   `null`: `table_params_snapshot_schema_invalid`;
7. `params` keys not exactly `_table_params_fields(snapshot_version)`;
8. any missing, extra or unknown key, and any value that violates the per-field
   type rules or the table bound: `table_params_snapshot_schema_invalid`;
9. only after 1–8 pass is `snapshot_sha256(doc.document)` compared with
   `expected_sha256`; a difference is `table_params_snapshot_sha_mismatch`.

A snapshot that fails 3–8 is `table_params_snapshot_schema_invalid` even if its
SHA matches itself. The three failure codes are disjoint: `parse_error` means
the bytes are not a UTF-8 JSON document, `duplicate_key` means they are a JSON
document with a repeated object key, and `schema_invalid` means a well-formed
JSON document whose root, `params` member, structure or values are not an
allowed snapshot. A non-object root or `params` is a structure failure, never a
parse failure.

Compatibility rules:

1. New runs use `table-params/v2`; the snapshot contains exactly `V2_FIELDS`
   (the 20 v1 names plus the seven logical names).
2. A replayed `table-params/v1` snapshot contains exactly `V1_FIELDS` and
   re-hashes to `82d4df4d...`; no logical key is added during replay.
3. `run_config.json` and `run_manifest.json` store `snapshot_version` and the
   snapshot hash. Audit and validation read that stored version, pass it as
   `expected_version` together with the stored hash as `expected_sha256`, and
   dispatch; they never call `table_params_snapshot(params)` without it. The
   stored version is what the validator is asked to accept, so a v1 artifact is
   never validated against the v2 field set.
4. `TableParams(**stored_v1_params)` remains valid because the new fields have
   defaults, but the reconstructed object is never re-dumped as v1.
5. An unknown version passed to the serializer raises
   `UnsupportedTableParamsSnapshotVersion` and is never guessed as v1 or v2;
   an artifact that stores an unknown version is rejected by the validator with
   `unsupported_table_params_snapshot_version`.
   `table_params_snapshot` and `table_params_sha256` refuse through the same
   `_table_params_fields` dispatch, so neither can emit or hash a snapshot
   labelled with an unknown version. A version mismatch between the snapshot
   and the manifest/run_config is `table_params_snapshot_version_mismatch`.
6. `configs/parser.yaml` is not edited. If the Reviewer later wants these
   defaults in YAML, that changes `parser_config_sha256` and requires a new run
   baseline; it is outside S2b.
7. `tools/audit_visual_primitives.py` still hashes the stored snapshot
   (`verify_identity`, `snapshot_sha256` over the loaded `document`), still
   checks `rule_primitives.py` and `GRID_TOL`, and still accepts
   `TableParams(**document["params"])`. Adding fields to `config.py` does not
   change `rule_primitives.py`, so the S2a identity gate is unchanged.
8. `tools.validate_evidence::validate_run` recomputes the hash from the stored
   snapshot, so old runs keep passing. It passes the
   raw artifact bytes to `validate_table_params_snapshot`, which loads them and
   recomputes the hash from the parsed document without a `TableParams`
   round-trip, and it reads visual parameters from the stored `params`; new
   logical keys do not affect that path.

**S2b-Schema edit boundary (N8).** "Do not modify S1/S2a" is refined into an
explicit allowlist so the implementing agent does not decide case by case:

| File | Allowed S2b-Schema change | Forbidden |
| --- | --- | --- |
| `src/icpdf/parser/config.py` | add the seven defaults; bump the version constant; add `V1_FIELDS` / `V2_FIELDS`, the two-branch version dispatch, the raw-bytes loader with its value object, and the strict validator | changing existing defaults or the v1 field list |
| `src/icpdf/parser/pipeline.py` | pass the version explicitly to snapshot/helpers | changing detection, extraction or run layout |
| `tools/audit_visual_primitives.py` | add read-only version dispatch and snapshot-schema validation | changing `verify_identity`, primitive/segment reconstruction, `GRID_TOL` binding or boundary checks |
| `tools/validate_evidence.py` | add the same read-only dispatch | changing existing checks or tolerances |
| `src/icpdf/parser/table_detector.py`, `structure.py` | additive logical fields; `_assign_words` may return its assignment mapping | changing `grid.xs`/`grid.ys`, cell construction, word assignment order or tolerance |
| `src/icpdf/parser/table_rebuilder.py` | fill logical ids/fields additively | changing existing table/row/cell/header id formats |
| `src/icpdf/parser/rule_primitives.py`, `visual_structure.py`, `table_regions.py` | none | any edit |
| `configs/parser.yaml`, Gold v1/v2, S1/S2a reports | none | any edit |

This is a compatibility layer only. S2a's primitive reconstruction, identity
gate and visual evidence checks stay byte-for-byte equivalent on old artifacts.

Required compatibility tests (S2b-Schema):

- replay a stored v1 snapshot and reproduce `82d4df4d...`;
- assert the v1 replay has no logical key;
- assert a v2 snapshot contains the seven logical keys;
- delete one v2 key and add one unknown key: each is refused although a SHA can
  still be computed;
- write a raw snapshot with a duplicate JSON key: `validate_table_params_snapshot`
  returns `table_params_snapshot_duplicate_key`; there is no entry point that
  accepts a plain `dict`, so the duplicate cannot be collapsed first;
- feed invalid UTF-8 bytes and a truncated JSON document: both return
  `table_params_snapshot_parse_error`, distinct from the duplicate-key code;
- feed a JSON array as the root, and a snapshot whose `params` is a string:
  both return `table_params_snapshot_schema_invalid`, never `parse_error`;
- call `table_params_snapshot` and `table_params_sha256` with `"table-params/v3"`:
  both raise `UnsupportedTableParamsSnapshotVersion`; neither falls back to v2;
- store `true` for `column_tolerance` and for `merge_shared_ratio`: both are
  refused even though `bool` is a subclass of `int`; store `1` for
  `merge_shared_ratio`: accepted as a JSON number and hashed as the canonical
  integer 1 without an int-to-float rewrite;
- a snapshot version that disagrees with the manifest is refused;
- run the S2a primitive audit on an old artifact and confirm zero identity
  errors;
- tamper the stored v1 snapshot and confirm the audit refuses;
- feed an unknown snapshot version and confirm refusal.

### 5.9 Interface comparison with `PHASE1_4_S2.md`

The umbrella design is the approved principle document, not a frozen schema.
This table makes every field-level difference explicit so the Reviewer can
accept or reject it before S2b-Schema.

| Umbrella `PHASE1_4_S2.md` | S2b proposal | Status |
| --- | --- | --- |
| `logical_boundaries: tuple[float, ...]` | unchanged, plus `logical_boundary_detail: tuple[LogicalBoundary, ...]` | type preserved; evidence is additive |
| `logical_columns: int \| None` | unchanged | aligned |
| `logical_mapping_status: str` | `"resolved" \| "unresolved"` | aligned |
| `column_projection` | `tuple[ColumnProjection, ...]`, authoritative | defined here |
| `logical_cells` | `tuple[LogicalCell, ...]`, with `PhysicalCellAssignment` | refined (R7) |
| `logical_headers`, `logical_header_path`, `logical_header_cells`, `logical_column_roles` | consolidated into `logical_columns_detail[i].header_path`, `.header_cell_refs`, `.role`, `.role_source`, `.role_header_cell_id` | **intentional consolidation**; avoids parallel arrays that can disagree (same failure class as P1-2) |
| `section_bands`, `condition_bands`, `condition_contexts` | absent | deferred to S2c |
| `DetectedCell.logical_cell_ids`, `.logical_columns`, `.word_ids` | unchanged derived caches | aligned |
| `Candidate.logical_cell_refs`, `.logical_columns` | unchanged additive fields | aligned |
| `TableParams.subrule_logical_span=0.85` | reuse existing `visual_full_height_coverage=0.85` | aligned by reuse |
| `TableParams.short_label_max_words`, `short_label_max_chars` | `logical_short_label_max_words`, `logical_short_label_max_chars` | renamed with `logical_` prefix |
| `TableParams.short_label_band_ratio=0.5` | `logical_subrule_promote_min_ratio=0.50` | renamed |
| `TableParams.crossing_epsilon_pt=0.5` | not introduced | S2c concern |
| `role_source` values | `header_text`, `subrule_short_label`, `heuristic`, `fail_closed`; `section_band` deferred | aligned with the existing field name and the approved promoted value |
| boundary sources | same five sources | aligned |

The only structural deviation is the consolidation of four per-column arrays
into one `logical_columns_detail` tuple. It is proposed because the arrays can
drift independently, exactly the problem P1-2 identified for `projection`.
Reviewer approval is requested for that consolidation in §14.

## 6. Candidate generation and decisions (deliverable 4)

### 6.1 Candidate set

Candidates are the union of:

1. internal positions of the frozen `grid.xs` (the recognition lattice);
2. S2a visual boundaries inside the table bbox;
3. header-canopy edges: left/right edges of `DetectedHeaderCell` bboxes that
   fall inside the table;
4. stable body gutters at x where at least `logical_label_min_bands` row bands
   have a gutter;
5. the two table bbox edges, always kept as `outer_left` / `outer_right`.

**Fixed-anchor grouping (N4).** Grouping is deterministic and cannot chain:

1. Sort candidates by `(x, source_rank, evidence_id)`, with `source_rank`
   `outer < grid < visual < header < gutter` and `evidence_id` the stable
   index/id inside that source. The sort is total; equal keys are impossible
   after de-duplication.
2. Take the first ungrouped candidate as the **anchor**. A candidate joins the
   group iff `abs(x - anchor_x) <= visual_boundary_tol_pt`. Always compare with
   the anchor, never with the previous member.
3. When a candidate exceeds the anchor distance, close the group and make that
   candidate the anchor of the next group.
4. The internal group x is the arithmetic mean of the member x values, with no
   rounding. Example: x = 100.0, 102.0, 104.0 with tolerance 2.5 yields
   `{100.0, 102.0}` and then `{104.0}`, never one chain of three.
5. `anchor_x` and every member `source_xs` are stored on the decision, sorted
   and unique. No source x is dropped or rewritten.
6. An outer boundary is its own group and its x is the table bbox edge, never
   the mean. A candidate within tolerance of an outer edge is folded into that
   outer group as extra evidence and is never kept as an internal boundary.
7. Candidates outside the table bbox are discarded before
   `LogicalBoundaryDecision` construction and recorded only in runtime
   diagnostic counters; they do not produce a decision record or a reason code.

This prevents several weak, non-coincident sources from being chained into one
strong boundary.

Outer boundaries are kept with `table_bbox` evidence. When
`boundary_source` is `implied_horizontal` / `implied_alignment`, they also carry
`region_extent` evidence; no vertical rule is fabricated.

No candidate is generated from a target count, a Gold value, a header label
alone or a cell's semantic content.

### 6.2 Decision table (R5)

For each grouped candidate, in deterministic x order:

| Evidence at x | Decision | Source |
| --- | --- | --- |
| within tolerance of an outer table edge | keep, `outer_*` | `structural` + `table_bbox` (+ `region_extent`) |
| S2a full-height printed rule (`coverage >= 0.85`) | keep | `printed_rule` |
| partial rule, `short_label_ratio >= logical_subrule_promote_min_ratio` (0.50) and `short_label_bands >= logical_subrule_promote_min_bands` (2) | keep | `subrule_promoted` |
| partial rule, `logical_subrule_ambiguous_min_ratio <= short_label_ratio < 0.50` and `nonempty_bands >= 2` | **unresolved** | — |
| partial rule, not promoted, and `condition_bands >= 1` | `demote_condition_path` | — |
| partial rule, not promoted, and `condition_bands == 0` | `demote_no_evidence` | — |
| no rule, aligned with a distinct header-cell gap/edge at `>= 1` header level | keep | `header_canopy` |
| no rule, stable body gutter with `len(grid_rows) >= logical_label_min_bands` and `gutter_ratio >= logical_label_min_band_ratio` | keep | `label_aligned` |
| no rule/header, candidate aligned with a repeated physical cell edge in `>= 2` distinct body grid rows (section-like rows excluded) | keep | `structural` |
| none of the above: no allowed logical-boundary evidence at x | `demote_no_evidence` | — |
| an internal candidate whose every supporting band is crossed by a body data cell or word (§5.3, §8.1) | **unresolved** | — |
| sources disagree on keep vs demote after grouping | **unresolved** | — |

The crossing row applies to every internal keep row above it, including a
full-height printed rule; outer boundaries are structural anchors and are
never vetoed. The veto is computed over the supporting bands of §5.3, so a
single crossed band removes only that band's support and does not by itself
make the table unresolved. `condition_bands` is the selected-run count of
§5.3/§6.5, never a scan of any right-side run.

**D14 objects and denominators.** Three objects stay distinct and are never
interchanged:

1. `BoundarySupport` counts body rows. `band_count = n_rows - header_rows`.
   `rule_bands` counts rows with `rule_at`; `gutter_bands` counts rows with a
   body gutter; `crossing_bands` counts supporting rows with a crossing body
   data cell or word. Header rows are outside `band_count`; section-like body
   rows stay inside `band_count` but are removed before the supporting count
   (§5.3.2) and never count as `rule_bands`, `gutter_bands` or a structural
   source.
2. `subrule_promoted` uses `nonempty_bands` = rows in `rule_bands` with at
   least one right-side word, and
   `short_label_ratio = short_label_bands / nonempty_bands`.
3. `subrule_partial` uses the same denominator, with
   `condition_bands` a subset of `rule_bands`.
4. `label_aligned` uses `gutter_ratio = gutter_bands / nonempty_bands`, where
   `nonempty_bands` counts body rows with at least one assigned word.
   `gutter_bands <= band_count`; a row with no word may still carry a gutter,
   so `gutter_ratio` may exceed 1.0 and is diagnostic, not an error.
5. `support_ratio = supported_bands / nonempty_bands` is diagnostic, may
   exceed 1.0 (including for `label_aligned`), and is `None` iff
   `nonempty_bands == 0`.

A `label_aligned` candidate that fails either threshold is `demote_no_evidence`
with `boundary_no_evidence`, and its `BoundarySupport` record is retained
unchanged. The failure is not `boundary_evidence_mismatch`.

A `colspan` body data cell is never evidence for a split. A crossing in a
header row or in a section-like body row does not veto a boundary supported in
ordinary body rows. A full-height
printed rule inside a body merged cell is conflicting physical evidence, not
proof of a split; when it is the only support and every supporting band is
crossed, the candidate is `unresolved` (`boundary_data_cell_crossing`).

### 6.3 Sub-rule promotion

The promotion test is the approved S2 rule, with the ratio defined exactly:

1. for each row band the rule intersects, the **source cell** is the unique
   `DetectedCell` whose bbox contains `x` (`bbox[0] <= x <= bbox[2]`) and whose
   row coverage includes that band. Zero source cells means no label candidate
   in that band; more than one is `subrule_source_cell_ambiguous` and the
   candidate is `unresolved`. Both endpoints are closed deliberately: `x` on a
   shared cell edge yields two cells and a fail-closed rejection. That outcome
   is intended and must not be "fixed" with a half-open interval, an epsilon or
   a tie-break by cell index;
2. inside the source cell take the words whose center is strictly right of x,
   sort them by `(x0, word_id)`, and start a new run whenever the gap to the
   previous word strictly exceeds `cell_gap_pt`, per §5.3.1; the parser
   `icpdf.parser.structure::_rule_grid` applies the same gap only when merging
   cells, and is not the normative definition;
3. let `m` be the smallest left edge among the right-side runs; select the run
   at `m`. Any run with `run_left - m <= 1e-6` is tied with it, so the
   candidate is `unresolved` (`subrule_run_tie`). The test is against `m` only
   and is never chained between runs; never pick a run by word count or text;
4. classify the selected run with §6.3.1; only `short_label` counts;
5. `nonempty_bands` = the number of bands **in `rule_bands`** with at least one
   word center strictly right of x inside the table, computed before
   classification. A band with an ambiguous or missing source cell still counts;
   the denominator is never "bands that produced a source cell";
6. `short_label_bands` = `len(label_assignments)`;
7. `short_label_ratio = short_label_bands / nonempty_bands` with
   `nonempty_bands > 0`; bands with no right-side word are excluded from both
   numerator and denominator and a band is never counted twice;
8. promote iff `short_label_ratio >= logical_subrule_promote_min_ratio` (0.50)
   **and** `short_label_bands >= logical_subrule_promote_min_bands` (2);
9. `logical_subrule_ambiguous_min_ratio <= ratio < 0.50` with at least 2
   non-empty bands is `unresolved`, not a demotion (lower bound inclusive,
   upper bound exclusive);
10. `nonempty_bands == 0` yields no ratio and no promotion; the candidate falls
    through to the no-evidence branch unless another source supports it.

#### 6.3.1 Lexical classes (N5)

Normalization: strip, collapse internal whitespace, and casefold only for
keyword matching; the stored label keeps its original text.

**Tokenization (N5-1).** A run is split on whitespace, then each fragment is
split by a left-to-right longest-match scan over four frozen token classes:

| Priority | Class | Tokens |
| --- | --- | --- |
| 1 | two-character operators | `>=`, `<=`, `..` |
| 2 | one-character operators and separators | `<`, `>`, `=`, `≈`, `≤`, `≥`, `–`, `—`, `±`, `%`, `(`, `)`, `,`, `.` |
| 3 | number | optional sign, digits, optional `.` plus digits, optional exponent |
| 4 | word | maximal run of Unicode letters, digits, `°`, `_`, `/`, plus `-` only under the asymmetric rule below |

Scanning is left to right. At each position the classes are tried in priority
order and the first class that matches wins; within a class the match is greedy.
This makes `>=` one token (class 1 before the class-2 `>`), turns `5..10` into
`5`, `..`, `10` (class-1 `..` before the class-2 `.`), and splits `0.8V` and
`10k` at the digit→letter boundary because class 3 is tried before class 4. A
letter→digit boundary does not split, so `CLK1` stays one token. `–` (en dash)
and `—` (em dash) are range dashes. Any character in no class is emitted as a
single `other` token, which no content class accepts. Markers are detected on
this token sequence, never by substring search of the normalized string.

**Word-run hyphen rule (R7).** A word run starts at a word-class character and
continues while the next character is a word-class character, or is `-` that
satisfies **both** conditions:

- the character immediately before the `-` is a Unicode letter, `_`, `°` or `/`
  — never a digit;
- the character immediately after the `-` is a word-class character (Unicode
  letter, digit, `°`, `_` or `/`).

The left condition is deliberately narrower than the word class. Digits are
word-class characters, so a symmetric "flanked by word characters" rule would
also absorb the hyphen of `5-10`, contradicting the required split; the rule
must not rely on that symmetry.

`+` and `-` that are not absorbed as above are tried as signs: a sign belongs
to a number token only at the start of a fragment or directly after an operator
token, and only when a digit or `.` follows. In every other position a `-` is an
`other` token; a `+` is then also `other`. A word run never starts with `-`.

**Operand grammar (N5-2).** Three productions are defined on the token
sequence:

- `value_phrase`: an optional unary `±` or `≈`, one number token, an optional
  multiplier token from `{k, M, G, m, µ, u, n, p}`, and an optional token from
  `LOGICAL_UNIT_TOKENS`, in that order — `5`, `5 V`, `10 kΩ`, `±0.5 %`;
- `operand`: a `value_phrase`, or exactly one word token (`A`, `VCC`, `CLK1`);
- `value_bearing`: a `value_phrase` only.

1. **range**: `value_bearing RC value_bearing`, `RC` in `{to, .., –, —,
   through}`; `to` and `through` are matched casefolded.
2. **symbol binding**: `SYM OP value_phrase`, `SYM` in the frozen
   `LOGICAL_SYMBOL_TOKENS` set below and `OP` one of the binary operators. The
   right side must be value-bearing, so `VCC = VDD` is not a symbol binding.
3. **binary comparison**: `operand OP operand`, `OP` in `{<, <=, >, >=, =, ≈,
   ≤, ≥}`, both operands non-empty. The sides need not be numeric, which is why
   `A=B` and `A>=B` are conditions.

**The relational marker is tested first, before any content class.** A run that
matches one of these productions is `condition_expression` and no later class
may claim it. Without this order a short, letter-bearing, digit-free run such
as `A=B` would be captured by `short_label` even though it states a relation.
Productions are tried in the order above; all three yield the same class, and
the order only fixes which description is recorded.

A run that matches none of the three productions — whether or not it contains
an operator token — is **not** condition-like: it is classified by the content
classes if one accepts the run, otherwise it is `unclassified`, contributes no
`short_label` and no condition signal. Unknown connectors, unknown symbols and
unclassifiable characters are never guessed; the candidate falls through to
`demote_no_evidence`.
A **unary** `±` or `≈` directly before a number is a tolerance, not a marker,
and a marker whose only operand sits inside the same parentheses does not make
the surrounding run a condition. No lexical outcome is `unresolved`:
`unresolved` is reserved for the geometric ambiguities of §6.3
(`subrule_source_cell_ambiguous`, `subrule_run_tie`) and the §6.2 conflict
rows; a lexically unrecognised run demotes, it does not block.

After the marker test, the content classes are applied in this order; the
first match wins:

| Class | Test |
| --- | --- |
| `condition_expression` | a relational marker above was found; decided before this table, listed here for completeness |
| `numeric` | an optional unary `±`/`≈` followed by exactly one number token, nothing else |
| `value_with_unit` | a `value_phrase` that contains a `LOGICAL_UNIT_TOKENS` token and no marker, e.g. `5 V`, `10 kΩ`, `±0.5 %`. This is data, not a condition |
| `unit_only` | exactly one `LOGICAL_UNIT_TOKENS` token, or one number followed by one multiplier token (`10k`, `100n`) |
| `identifier` | one token matching `[A-Za-z][A-Za-z0-9_/-]*` that contains a digit or `_`/`/`, with no whitespace |
| `short_label` | at most `logical_short_label_max_words` tokens and `logical_short_label_max_chars` characters, at least one letter token, no number token, and not `unit_only` |
| `field_name` | a plain noun phrase with no marker, no operator token and no number token, e.g. `Output Voltage`, `Clock Source`, `Data Format`, `Input Range`, `Operating Mode` |
| `prose` | more than six tokens or sentence punctuation, and no marker |

Worked examples, decided by this grammar alone:

| Run | Tokens | Production | Class |
| --- | --- | --- | --- |
| `A=B` | `A` `=` `B` | binary comparison | `condition_expression` |
| `A>=B` | `A` `>=` `B` | binary comparison, `>=` matched whole | `condition_expression` |
| `VCC=5V` | `VCC` `=` `5` `V` | symbol binding | `condition_expression` |
| `VIL<0.8V` | `VIL` `<` `0.8` `V` | binary comparison | `condition_expression` |
| `5V–10V` | `5` `V` `–` `10` `V` | range | `condition_expression` |
| `5..10 V` | `5` `..` `10` `V` | range, `..` matched whole | `condition_expression` |
| `5 V to 10 V` | `5` `V` `to` `10` `V` | range | `condition_expression` |
| `TA = 25 °C` | `TA` `=` `25` `°C` | symbol binding | `condition_expression` |
| `±0.5 %` | `±` `0.5` `%` | none, unary tolerance | `value_with_unit` |
| `10k` | `10` `k` | none | `unit_only` |
| `VIN = 5 V` | `VIN` `=` `5` `V` | binary comparison | `condition_expression` |
| `A ~ B` | `A` `~` `B` | none, unknown operator | `unclassified`, demotes |
| `V-10V` | `V-10V` | none, one token | `identifier`, demotes |
| `5V-10V` | `5` `V-10V` | none, two tokens | `unclassified`, demotes |

`VIN = 5 V` is a condition by the generic binary rule only. It receives no
supply or temperature semantics, and it is not a symbol binding.

**Tokenizer test vectors (N5-1).** These are normative; an implementation must
produce exactly these token sequences:

| Fragment | Tokens | Rule exercised |
| --- | --- | --- |
| `>=` | `>=` | class 1 beats the class-2 `>` |
| `<=` | `<=` | class 1 beats the class-2 `<` |
| `5..10` | `5` `..` `10` | class-1 `..` beats the class-2 `.` |
| `5.5..6.5` | `5.5` `..` `6.5` | decimal point stays inside the number token |
| `-5` | `-5` | sign at fragment start, digit follows |
| `2>=-5` | `2` `>=` `-5` | sign directly after an operator token |
| `5-10` | `5` `other(-)` `10` | left neighbour is a digit, so the hyphen is not absorbed |
| `CLK-1` | `CLK-1` | left neighbour is a letter, right neighbour a digit |
| `CLK-ABC` | `CLK-ABC` | letters on both sides |
| `CLK-` | `CLK` `other(-)` | no right neighbour, so no absorption |
| `5V-10V` | `5` `V-10V` | left neighbour `V` is a letter, right neighbour `1` is a digit |
| `5 V -10 V` | `5` `V` `-10` `V` | whitespace first; `-10` is a signed number at fragment start |
| `10k` | `10` `k` | digit→letter split, standalone multiplier |
| `10 kΩ` | `10` `kΩ` | unit token stays intact |
| `10kΩ` | `10` `kΩ` | `kΩ` is one unit token; no multiplier is extracted from it |
| `0.8V` | `0.8` `V` | number class before word class |
| `±0.5 %` | `±` `0.5` `%` | unary tolerance tokens |

Two consequences are normative and not defects:

- `5V-10V` yields `5`, `V-10V`, not a split value. ASCII `-` is not a range
  connector, so the run is **not** a range. It is also **not** `identifier`:
  the run has two tokens and `identifier` accepts only a one-token run (§6.3.1
  below). No content class accepts the two-token run, so the run is
  `unclassified` and the candidate demotes with no evidence.
- `5 V -10 V` yields `5`, `V`, `-10`, `V`. There is no connector token, so no
  production matches, and the run is `unclassified` and demotes. A range needs
  an explicit connector (`to`, `through`, `..`, `–`, `—`); juxtaposition of two
  values is never inferred as a range.

**`identifier` is a single-token class (R8).** Every content class is tested
against the **whole run's token sequence**, never against one token lifted out
of a run. `identifier` accepts a run only when all three conditions hold:

- the run consists of exactly one token;
- that token matches `[A-Za-z][A-Za-z0-9_/-]*`;
- the token contains a digit, `_` or `/`.

A `-` inside a word run can therefore create an identifier-shaped *token*
without making the containing *run* an identifier. The outcomes are exhaustive:

| Run | Tokens | Class | Why |
| --- | --- | --- | --- |
| `V-10V` | `V-10V` | `identifier` | one token, regex match, contains a digit |
| `CLK-1` | `CLK-1` | `identifier` | one token, regex match, contains a digit |
| `CLK-ABC` | `CLK-ABC` | `short_label` | one token but no digit, `_` or `/` |
| `5V-10V` | `5`, `V-10V` | `unclassified` | two tokens, so `identifier` cannot accept the run; `short_label` and `field_name` reject a number token; two tokens are not `prose` |
| `5 V -10 V` | `5`, `V`, `-10`, `V` | `unclassified` | no production matches and no class accepts four tokens with numbers |

The token `V-10V` is identifier-shaped, but class membership is a property of
the run, not of a token. This is not a new rule; it is the "one token … with
no whitespace" wording of the class table applied to the run.

`identifier` is terminal and has exactly these downstream effects:

| Effect | Value |
| --- | --- |
| counts in `label_assignments` | no; only `short_label` does (§6.3 step 4), so `identifier` never raises `short_label_ratio` and never contributes to promotion |
| condition signal | none; `identifier` is not condition-like (§6.5), so it adds zero to `condition_bands` and cannot by itself produce `demote_condition_path` |
| S2c output | none; a lexical class emits no `ConditionBand`, no `ConditionContext` and no text |
| boundary outcome when the run is the right-side evidence | contributes zero to `condition_bands`; the candidate is decided by the §6.2 count, so this run alone yields the no-evidence branch, `demote_no_evidence`, reason `boundary_no_evidence` |
| override of the ratio branch | never; the order of §6.5 stands, and a class never overrides promote/ambiguous |
| `unresolved` | never; a determinate class rejection is not an ambiguity |

**Class disjointness (N5-2).** `numeric`, `value_with_unit` and `unit_only` are
disjoint by token count, so the class table order only makes precedence
explicit:

- `numeric` is exactly one number token, optionally preceded by a unary
  `±`/`≈`;
- `value_with_unit` is a `value_phrase` that contains a `LOGICAL_UNIT_TOKENS`
  token;
- `unit_only` is exactly one `LOGICAL_UNIT_TOKENS` token, or one number followed
  by one multiplier token.

The multiplier tokens `{k, M, G, m, µ, u, n, p}` are frozen and are never
physical units: `10k` carries no unit, and `10 kΩ` is a complete
`value_phrase`. A multiplier counts only as a **standalone token**. A token
already in `LOGICAL_UNIT_TOKENS` is never re-split to extract a multiplier:
`kΩ` stays one unit token and its leading `k` is not a multiplier, so `10kΩ`
is `10`, `kΩ` and is `value_with_unit`, while `10k` is `10`, `k` and is
`unit_only`.

`unit_only` is a lexical content class, not a physical-quantity judgement; it
states only that the run carries no standalone value usable as a parameter.

`LOGICAL_UNIT_TOKENS` is a frozen code constant, not a YAML entry. Its initial
closed set is:

```text
V, mV, µV, uV, kV, A, mA, µA, uA, nA, W, mW, µW, kW,
Ω, kΩ, MΩ, ohm, Hz, kHz, MHz, GHz, s, ms, µs, us, ns, ps,
F, pF, nF, µF, uF, mF, H, nH, µH, %, °C, °F, K, dB, dBm,
LSB, ppm, V/V, A/A, °, rad, S, mS, µS
```

The set may be extended only with a new design review; it may not be tuned
after seeing S2b results.

`LOGICAL_SYMBOL_TOKENS` is likewise a frozen code constant, not a YAML entry,
and its closed set is exactly:

```text
VCC, VDD, VIL, VIH, TA, TJ
```

Matching is casefolded. No other token is a symbol binding: `VIN`, `VOUT`,
`VEE`, `VSS`, `TEMP`, `CLK` and `EN` are deliberately excluded, so a run such
as `VIN = 5 V` is an ordinary binary comparison with no supply or temperature
semantics attached. Extending this set requires a new design review; it may not
be tuned after seeing S2b results.

**Only `condition_expression` is condition-like.** `field_name` and marker-free
`prose` are never demoted to `condition_path` merely because they contain
letters or are longer than a short label.

Measured examples from the approved design:

- CY29FCT520 P06 `290.2` (coverage 0.576), right-side `Data` / `I` in 4 of 5
  bands -> promote, 6 -> 7 logical columns.
- CY29FCT520 P05 `193.9`, `266.0`, right side is condition prose -> demote to
  condition path.
- DS10CP152 P04 `346.1`, P05 `363.1`, right side is numeric/unit content ->
  demote with no semantic claim.

No threshold may be adjusted after seeing S2b results; changes require a new
design review.

### 6.4 Header-canopy boundaries

A header canopy can create a logical boundary with no printed rule. The
boundary is kept only when:

- at least one header level has a gap or cell edge at x within
  `visual_boundary_tol_pt`;
- the header cells on the two sides carry distinct labels (not two fragments of
  the same text run);
- the resulting interval contains at least one header cell or data cell; an
  entirely empty interval is not created by a header gap alone.

Example: CY29FCT520 P04 has four logical boundaries (362.9, 393.2, 452.6,
482.9) that exist only as header-canopy boundaries, giving 8 logical columns
against 4 visual columns. These x positions are added to the logical lattice
only; `grid.xs` is untouched.

### 6.5 Demotion semantics (R5, P0-3)

The previous design assigned `demoted_to = "condition_path"` to every demoted
candidate. That gave condition semantics to unrelated rejected boundaries. The
split is:

**`demote_no_evidence`** — no allowed evidence for a logical split.

- `demoted_to = "no_evidence"`, `reasons` includes `boundary_no_evidence`.
- Used for speculative `grid.xs` soft splits and for candidates with no
  rule/header/label/structural evidence.
- A non-promoted partial rule whose right side is numeric/unit content also
  lands here (for example DS10CP152 P04/P05). The `support` record still shows
  `rule_bands`; the name means "no evidence for a logical split and no S2c
  semantic claim", not "no printed rule".
- No S2c condition band is created.

**`demote_condition_path`** — an internal partial sub-rule with condition-like
right-side text.

- `demoted_to = "condition_path"`,
  `reasons = ("boundary_condition_subrule",)`.
- Preconditions: the candidate is internal; it has a partial printed rule
  (`0 < coverage < visual_full_height_coverage`); it was not promoted; the
  short-label ratio is below `logical_subrule_ambiguous_min_ratio` (otherwise the
  ambiguous branch already wins); `condition_bands >= 1`.
- `condition_bands` is the count of bands whose **selected nearest right-side
  run** is condition-like, using the one run §6.3 steps 2–3 select for each band
  and the `nonempty_bands` set of §6.3 step 5. A band with no right-side word,
  or with zero source cells (so no selected run), contributes zero. Other
  right-side runs in the same band are never inspected. Both the demotion-
  condition row of §6.2 and this precondition use this same count; there is no
  separate "any run" test.
- "Condition-like" means that selected run is classified
  `condition_expression` by §6.3.1 and carries at least one **relational**
  marker (comparison operator, range connector, or a supply/temperature symbol
  bound by such an operator). A `field_name` such as `Output Voltage` or
  `Clock Source`, a marker-free `prose` run, `numeric`, `value_with_unit`,
  `unit_only` and `identifier` are **not** condition-like; `5 V` alone is a
  data value. This is the only content test in S2b; it does not read a cell's
  semantic category.
- A band with `subrule_source_cell_ambiguous` or `subrule_run_tie` makes the
  whole candidate `unresolved` before the condition test, so it never becomes
  `demote_condition_path`; a band with zero source cells is not condition-like
  but does not alone block demotion.
- Each selected run is classified independently. A run contributes one to
  `condition_bands` only when its lexical class is `condition_expression` and it
  carries at least one explicit relational marker. A selected run that is
  ambiguous, marker-free, or of another lexical class contributes zero and does
  not by itself decide the candidate.
- The candidate-level decision is exclusive to the `condition_bands` count in
  §6.2: `condition_bands >= 1` yields `demote_condition_path`;
  `condition_bands == 0` yields `demote_no_evidence`. The unresolved
  preconditions above (source-cell ambiguity, run tie) take precedence over
  both, so no band-level class result can override the candidate-level count.
- `condition_path` is a **path label** for S2c. S2b emits no `ConditionBand`
  and no `ConditionContext`; it only preserves the demoted x, its row bands and
  its support for the later S2c stage.

The order is fixed: promote, then the short-label ambiguity branch, then
`condition_bands >= 1` (`demote_condition_path`), then `condition_bands == 0`
(`demote_no_evidence`). A boundary whose selected runs are condition-like but
which also lands in the ambiguous ratio window `[0.25, 0.50)` stays
`unresolved`, not `demote_condition_path`; a content class never overrides the
ratio branch.

**`ConditionPathRecord` (D2).**

```text
ConditionPathRecord
  condition_path_index: int            # position in logical_condition_paths
  decision_index: int                  # position in logical_boundary_decisions
  candidate_x: float
  anchor_x: float
  source_xs: tuple[float, ...]
  row_bands: tuple[int, ...]           # condition-bearing body rows; absolute grid rows
  support: BoundarySupport
  partial_rule: SubrulePartialEvidence
```

`ConditionPathRecord` is the only authoritative condition-path payload. A
record exists iff its referenced decision has
`decision == "demote_condition_path"`; the relation is a bijection:

- every `demote_condition_path` decision has exactly one record;
- every record references exactly one such decision;
- no two records share a `decision_index`;
- `condition_path_index` equals the record's 0-based position, and
  `decision_index` is strictly ascending.

Scalar fields are copied from the referenced decision: `candidate_x`,
`anchor_x`, `source_xs` and `support` verbatim; `row_bands` equals
`partial_rule.condition_bands`, is non-empty, ordered, unique and body-only.
The referenced decision's `evidence` must contain exactly one
`kind == "subrule_partial"` member, and `partial_rule` must equal it field for
field. Zero or several members, an unequal copy, or unequal `row_bands` is
`condition_path_decision_mismatch`.

Three row sets are not interchangeable:

- `LogicalBoundaryDecision.row_bands`: every body grid row;
- `ConditionPathRecord.row_bands`: condition-bearing body rows, equal to
  `partial_rule.condition_bands`;
- `SubrulePartialEvidence.condition_bands`: the same condition-bearing rows.

The record's `row_bands` is a subset of the decision's, usually a strict
subset; the validator checks both the subset relation and equality with the
evidence. `BoundarySupport.condition_bands` is a count, not a set, and is never
compared with these tuples.

**Two-stage decision and unresolved withholding (D2).**

1. Stage A classifies each candidate by §6.2 without knowing whether another
   candidate or a mapping check will fail. A candidate may become
   `demote_condition_path` here.
2. Stage B runs after all candidates and all mapping checks. If any candidate is
   `unresolved`, or any logical-payload check of invariant 21(e) fails, the
   table is unresolved (§10.1).
3. On an unresolved table, every Stage A `demote_condition_path` is rewritten to
   `demote_no_evidence`: `decision = "demote_no_evidence"`,
   `demoted_to = "no_evidence"`. The Stage A `reasons` are preserved in their
   original order; no member is removed, reordered or de-duplicated.
   `condition_path_withheld_unresolved` is appended once at the end.
   `boundary_no_evidence` is appended only if it was already present in Stage A;
   a withheld condition path does not add it. `row_bands` remains the standard
   all-body-row tuple, the Stage A condition rows remain available in the
   retained `subrule_partial` evidence, and `evidence` is unchanged with exactly
   one `subrule_partial`.
4. `condition_path_withheld_unresolved` is reserved for Stage B. Stage A must
   never emit it. On a rewritten decision it occurs exactly once and is the
   final reason. A normal Stage A `demote_no_evidence` must contain
   `boundary_no_evidence`; only the Stage B withholding state may omit it.
5. No decision on an unresolved table has `decision == "demote_condition_path"`,
   and `logical_condition_paths` is empty. A record on an unresolved table is
   `condition_path_decision_mismatch`.
6. On a resolved table the bijection applies unchanged, and
   `condition_path_withheld_unresolved` may not appear.

`demote_no_evidence` with `demoted_to = "no_evidence"` in Stage B is a closed
state meaning "no condition path may be emitted"; it is not a claim that the
candidate lacked evidence. `condition_path_withheld_unresolved` is the only
permitted reason why a `demote_no_evidence` decision omits
`boundary_no_evidence`; the validator accepts that exception only when the code
is present.

## 7. Physical→logical mapping (deliverable 2)

### 7.1 One physical lattice per table (R3, P0-1)

`PhysicalColumnOverlap.physical_column` is a 0-based interval index into the
**one** `grid.xs` of the table that produced the `DetectedTable` (§3.2). The
premise of the previous §6.2 — that regions may use different physical x
lattices — is not true in the current repository:

- `detect_tables()` maps one `TableRegion` to one `TableGrid` to one
  `DetectedTable`;
- `_region_from_cluster()` already merged stacked components into one region;
- `_rule_grid()` builds one `all_xs` and one `TableGrid`;
- `region_components` lists the merged components for provenance only.

Therefore `physical_column` is unique within the table, and
`region_component_ids` never selects a different lattice. `physical_left` /
`physical_right` are the self-checking locator, and the validator re-derives
`grid.xs` from a fresh parse.

**Out of scope:** aggregating separate `DetectedTable`s (for example a
cross-page continuation) into one logical table. If that is ever required, a new
design must introduce a table-level `physical_lattice_id` / lattice hash and a
region-local `(region_id, local_column_index, xs_left, xs_right)` tuple. S2b
does not do this, and no S2b field may be read as a region-local index.

### 7.2 Interval mapping

`ColumnProjection` is overlap-based, not a partition:

- one logical column may contain several physical columns (demoted sub-rules,
  wide condition columns);
- one physical column may be split into several logical columns (promoted
  sub-rules, header canopies);
- a logical column may span several physical columns across row bands within
  the same table.

For each logical column `[left, right]` and each `BandObservation`, record one
`PhysicalColumnOverlap` for every physical column in `occupied_columns(band)`
that has positive width overlap with `[left, right]`. An empty band, or a band
whose occupied columns do not intersect the interval, records nothing. The
records are sorted by `(band_index, physical_column)`. `overlap_fraction` is
recomputed from `overlap_left`, `overlap_right` and the physical width; a
mismatch is an error, not a warning. The `logical_row_bands` themselves still
partition `[0, n_rows - 1]` exactly; the overlaps are a coverage relation over
occupied cells, not a partition of bands. Adjacent bands may carry the same
physical column set; set equality never merges bands.

`physical_column` plus `physical_left` / `physical_right` is the locator.
`band_index` plus `grid_row_start` / `grid_row_end` is the canonical band, not
an arbitrary text extent.

### 7.3 Cell projection and word assignment

1. For each row and logical column, find physical cells whose bbox has a
   positive-width intersection with the logical interval. "Row" means the
   logical row index `0 .. n_rows - 1` of the persisted `grid_ys` lattice
   (D6), never a position in the sparse `rows` list; `DetectedRow.grid_row`
   already carries that index.
2. Assign each `TextWord` by its exact center x:
   `cx = (bbox[0] + bbox[2]) / 2`. Two preconditions precede every interval
   test. A non-finite center is `mapping_word_not_assigned` and the table is
   unresolved. A center outside the closed outer extent, `cx < b[0]` or
   `cx > b[-1]`, is `mapping_word_outside_logical_extent` and the table is
   unresolved; there is **no clamp, snap, tolerance or boundary widening**.
   This case is reachable: `icpdf.parser.structure::_assign_words` accepts a
   word when its center is within `0.8` pt of a cell edge, so a word can belong
   to a physical cell while its center lies just outside the outermost logical
   boundary; the two decisions are independent and the mapping one fails
   closed. Inside the extent every logical column uses the left-open,
   right-closed interval `(b[i], b[i + 1]]`; the single point `cx == b[0]` on
   the left outer edge is assigned to column 0. A center exactly on an internal
   boundary (`cx == b[i]`) therefore belongs to the left column `i - 1`. There
   is **no epsilon and no rounding**: coordinates are
   compared as stored floats. Every exact-boundary hit increments the
   `word_boundary_tie` diagnostic count once for that word, but the assignment
   is still the one above; the count is neither a reason code nor a persisted
   assignment field, and it never makes a table unresolved (§10.2).
3. Decompose physical cells into logical cells by §5.6: one logical cell per
   (physical cell, maximal consecutive run of word-bearing logical columns),
   merged only when `(row_start, row_end, logical_column,
   logical_column_span)` is identical. A physical cell straddling a boundary
   appears in several `PhysicalCellAssignment`s with the same
   `PhysicalCellRef` and disjoint word subsets; no word is duplicated.
4. `word_ids` across all logical cells are a disjoint partition of the word
   universe defined in §5.6, item 5.

**D4 verifier (implemented, not yet wired).**
`icpdf.parser.structure::assign_words_to_logical_columns` is item 2 as a pure
function. It requires at least two
boundaries and rejects a non-finite or non-strict lattice with `ValueError`. Per word it
raises `LogicalMappingError` carrying one of three codes and the `word_id`:
`mapping_word_not_assigned` for a non-finite center,
`mapping_word_outside_logical_extent` for a center outside the closed outer
extent, and `mapping_word_partition_mismatch` for a duplicate id. Otherwise it
returns `WordColumnAssignment`, whose `columns` map `word_id -> column` and
whose `boundary_ties` tuple lists every word whose center equals any boundary
exactly once. `detect_tables` does not call it in this slice because logical
boundaries are derived in S2b-2; the function is the frozen contract that
integration must call instead of re-implementing the interval test.

**D6 row lattice (implemented, additive).**
`icpdf.parser.table_detector::detect_tables` copies `grid.ys` verbatim into
`DetectedTable.grid_ys` and `grid.n_rows` into `DetectedTable.n_rows`;
`icpdf.parser.table_rebuilder::build_table` copies both to the domain `Table`.
`rows` stays sparse: `detect_tables` skips a grid row with no non-empty cell,
so `len(rows) <= n_rows` and `len(rows)` is **not** the row count.
`DetectedRow.grid_row` is the logical row index, not the sparse position. One
shared function, `icpdf.domain.table::validate_grid_ys`, is called by both the
domain `Table` validator `icpdf.domain.table::_check_table` and the parser
`DetectedTable` validator in `icpdf.parser.table_detector`. A non-empty lattice
needs at least two coordinates,
`n_rows >= 1`, every coordinate finite, `len(grid_ys) == n_rows + 1`, and
strictly ascending adjacent pairs (`right` greater than `left`); an empty
lattice requires `n_rows == 0`. "Non-decreasing" is not acceptable because
the closed D3 lattice is strictly ascending. Legacy artifacts keep the empty
defaults and bypass the non-empty rules.

The per-cell assignment is the R7/P1-1 fix. A `LogicalCell` cannot be
reconstructed from `physical_cell_refs` plus a flat `word_ids` list, because
that does not say which words of a shared physical cell belong to which logical
cell. `PhysicalCellAssignment` does.

A physical cell may be referenced by several logical cells (header canopy,
section-like spanning cell, or word-level split). The reverse cache on the
physical cell lists all of them.

### 7.4 Mapping examples

- CY29FCT520 P04: visual column 1 contains logical MIN/NOM/MAX; one physical
  column maps to three logical columns.
- CY29FCT520 P05: visual columns 1–3 form one condition logical column; three
  physical columns map to one logical column.
- MICRF103 P03: six visual columns and six logical columns; the outer edges are
  implied, not printed, and the mapping must not invent a seventh column.

## 8. Merged cells and multi-level headers (deliverable 3)

### 8.1 `colspan`

`column_span` is a physical fact and never creates or removes a logical
boundary by itself.

- A header cell with `column_span > 1` is a canopy cover. It backs every logical
  column it covers; the same `HeaderCellRef` appears in each covered logical
  column's `header_cell_refs`, so the cover relation stays visible without a
  separate flag.
- A body data cell whose bbox crosses a candidate boundary, whether or not it
  has `column_span > 1`, is treated band by band: that band does not support
  the boundary, and the candidate's `crossing_bands` increments once for that
  band. A body word bbox that strictly straddles x counts the same way. This
  is the single veto rule shared with §5.3 and §6.2: the candidate is
  `unresolved` (`boundary_data_cell_crossing`) only when every supporting band
  is crossed; otherwise crossing alone does not veto the candidate. The
  remaining keep/demote decision is still determined by the applicable evidence
  and decision rules of §6.2, and the crossed bands contribute no surviving
  support. A printed full-height rule inside a merged data cell is conflicting
  physical evidence and does not rescue an all-crossed candidate; there is no
  printed-rule or header-canopy tie-break.
- A section-like body row is identified by the geometric predicate of §5.3.2,
  never by text. The row is removed before any supporting-band count, so a
  crossing there is not a supporting row and does not veto a boundary supported
  in ordinary body rows. The row is not removed from `band_count` or
  `row_bands`: it is still a body row of the table, so it counts in
  `band_count` but in neither `supporting_bands` nor `crossing_bands`. Its
  cells are projected to the logical cells they overlap but never count as
  `rule_bands`, `gutter_bands` or a structural source. Header rows are exempt
  by range. S2b does not assign section semantics; that is deferred to S2c.

### 8.2 Multi-level headers

- Header levels are read from the existing `DetectedHeaderCell.level`.
- For each logical column `[L, R]` and each level, compute the x-overlap width
  of every header cell at that level:

  ```text
  width(cell) = max(0, min(cell.bbox[2], R) - max(cell.bbox[0], L))
  ```

  Only cells with `width > 0` are candidates. The winner is the maximum width;
  two candidates whose widths differ by at most `1e-6` are a tie, and the table
  is `unresolved` (`header_level_tie`). Width, not area or bbox centre, is the
  only criterion.
- `header_path` is the top-to-bottom list of winning labels, ordered by
  `level`. Missing levels are skipped, not filled from neighbours;
  `header_cell_refs` is parallel to `header_path` and records exactly which
  printed cells supplied each label.
- A canopy cell may appear at the same level for several logical columns; that
  is intentional and is not a duplicate-header error.
- Header text is never split or rewritten. Logical header attribution only
  references existing printed cells.

### 8.3 Blank and headerless areas

- A fully ruled, entirely blank physical column stays in the logical lattice
  with `role = "unknown"`; its boundaries are kept as `printed_rule` because the
  full-height printed rules are the evidence.
- A wide blank gutter with no rule, no header and no stable body gutter is not
  a candidate and cannot create a logical column. If such an x came from a
  speculative `grid.xs` soft split, it is `demote_no_evidence`; a full-height
  printed rule is handled by the first bullet, not by this one.
- A table with no header at all may still get a `resolved` logical lattice from
  printed rules and body gutters; header paths are empty and are not a failure.

## 9. Evidence chain (deliverable 5, R7)

### 9.1 Walkable chain

Every accepted logical fact must be walkable back to the source:

```text
LogicalBoundary
  -> LogicalBoundaryEvidence (discriminated union)
     -> S2a VisualBoundary / VisualSegment (by index)
        -> VisualSegment.primitive_indices (page-level collect_primitives)
     -> DetectedHeaderCell (level, source_row, source_column, bbox)
     -> grid rows and TextWord.word_id
LogicalColumn
  -> ColumnProjection -> PhysicalColumnOverlap
     -> physical_column + physical_left/right (the table's one grid.xs)
     -> region_component_ids (provenance)
  -> HeaderCellRef -> DetectedHeaderCell
LogicalCell
  -> PhysicalCellAssignment -> PhysicalCellRef
     -> DetectedRow.grid_row + index in DetectedRow.cells
     -> domain cell_id after rebuild
  -> word_ids -> TextWord.word_id (deterministic page-level id)
     -> TextWord.bbox and block/line indices
```

No logical record may carry an x, label or text that is not backed by one of
these references. `LogicalBoundaryEvidence.visual_segment_indices` uses the S2a
record by index rather than copying primitive indices, so there is one primitive
provenance chain, not two.

### 9.2 Reference resolution rules

The read-only audit re-resolves every reference against a fresh parse:

- `visual_boundary_index`: in range of `visual_boundaries` /
  `visual_boundary_evidence`; the x at that index is within
  `visual_boundary_tol_pt` of the logical boundary; the role matches the S2a
  boundary role and the logical role.
- `visual_segment_indices`: in range of the referenced `VisualBoundary.segments`;
  each segment resolves to a `VisualSegment` with the same `component_id`,
  `y0`, `y1`; the component id is in `region_components`; the segment span is
  inside the table bbox.
- `header_cell_refs` resolve in two ordered steps (D15). Step 1 is identity:
  the key `(level, source_row, source_column, column)` is matched against every
  `DetectedHeaderCell` of this table. Zero matches is
  `boundary_evidence_missing_ref`; more than one match is
  `header_ref_ambiguous` (code 27); exactly one match proceeds to step 2.
  Step 2 is content: `text` and `bbox` must equal the matched cell, and
  `level < header_rows`; any mismatch is `boundary_evidence_mismatch`. The two
  steps never swap and never merge: identity failure is not relabelled as a
  content mismatch, and a content mismatch is not relabelled as a missing ref.
  For `header_canopy`, every left ref satisfies `bbox[2] <= x + tol`, every
  right ref `bbox[0] >= x - tol`, each anchor is the head of its nearest-first
  list, the anchors satisfy the `boundary_edge` rule of §5.3, and
  `left_label` / `right_label` equal the anchors' normalized text. A repeated
  ref inside one declared list is `boundary_evidence_duplicate_ref`; a
  geometric tie between two header cells at one level is `header_level_tie`; an
  empty required side list is `header_missing_for_canopy`. These three checks
  are distinct from step 1 and from each other.
- `subrule label_assignments`: `grid_row`s are unique and inside `rule_bands`;
  each `physical_cell_ref` resolves; each word id is in that cell and strictly
  right of x; `selected_run_bbox` equals the word union; `nonempty_bands` and
  `short_label_ratio` recompute from the fresh parse.
- `table_bbox`: `page_number` and `table_bbox` equal the fresh `DetectedTable`
  exactly; a mismatch is stale, not a warning.
- `region_extent`: the region is resolved first, by component-id equality with
  `set(table.region_components)` over the fresh `detect_table_regions` output.
  Zero matches is `boundary_evidence_missing_ref`; more than one is
  `region_lattice_inconsistent`; `source`, `boundary_source` or page mismatch is
  `boundary_evidence_stale`. Only then does `implied_outer_evidence_index`
  select `TableRegion.evidence[kind="implied_outer"]` inside that region, and
  `implied_outer_values`, `extent_left/right`, `region_component_ids`,
  `boundary_source` and `page_number` must match that record.
- `grid_rows`: in `[header_rows, n_rows)`; each row is a real band; no row is
  repeated.
- `word_ids`: each id exists exactly once on the page. Membership is checked
  three times under one code and three distinct rules (§11.0, W-1, W-2a, W-2b):
  W-1 requires the word centre inside the closed outer extent with no
  tolerance, clamp, snap or boundary widening; W-2a requires it inside the
  referenced physical cell bbox with the 0.8pt inclusive tolerance of
  `_assign_words`; W-2b requires it inside the logical cell bbox with the same
  0.8pt inclusive tolerance. The rules are not interchangeable: W-1 never
  inherits 0.8pt and W-2a / W-2b never inherit the closed-extent rule. A word
  centre that is not finite belongs to `mapping_word_not_assigned` (§5.6).
  Across every `PhysicalCellAssignment` of the table a word id appears at most
  once. If one physical cell is referenced by more than one logical cell, those
  assignments must carry disjoint `word_ids` sets; the union over the table
  equals the recomputed word universe of §5.6.
- `physical_cell_edge_refs`: `(grid_row, cell_index)` resolves to a real
  `DetectedCell`; `column_index` matches; the edge x is within tolerance of the
  logical boundary; refs are sorted and unique per `(grid_row, cell_index,
  edge)`; refs sharing `(grid_row, edge)` form one group whose span
  `max(edge_xs) - min(edge_xs)` is within `visual_boundary_tol_pt`; at least two
  distinct `grid_row` values remain across groups.
- `physical_column`, `physical_left`, `physical_right`: `physical_column` is a
  valid interval index; `physical_left == grid.xs[i]` and `physical_right ==
  grid.xs[i + 1]`. Overlaps reference the table-level layout bands through
  `band_index`: the index is in range, the band shape is non-empty,
  `grid_row_start` and `grid_row_end` equal the band exactly, and
  `physical_column` is in `occupied_columns(band)`. The layout bands partition
  `0 .. n_rows - 1`: a signature run that is not maximal is 5.4a, an uncovered
  row between two bands is 5.4b, and an intersection or duplicate is 5.4c, both
  the latter reported as `mapping_row_band_overlap`. Within one
  `(band_index, logical_column)` pair `physical_column` is unique and
  ascending. 6.1a checks range and 6.1b checks recompute:
  `overlap_left`, `overlap_right` and `overlap_fraction` must recompute from the
  authoritative logical interval and physical width within `1e-6`, and that
  recompute is an A failure, not a reason code.
- `visual_column_indices`: `len(visual_boundaries) == visual_columns + 1` when
  not `None`; indices are sorted, unique and in range; each has positive width
  overlap by the §5.4 rule.
- `region_component_ids`: every id is in `region_components`; for
  `region_extent`, the structured fields match the fresh `TableRegion`
  evidence as above.

### 9.3 Independent reconstruction of a logical cell

Given a persisted `LogicalCell`, an independent reader can rebuild it without
running the S2b decision logic:

1. take `physical_cells`; for each `PhysicalCellAssignment`, resolve
   `PhysicalCellRef` to a physical cell and take exactly the listed `word_ids`;
2. resolve each word id to its `TextWord` (page, block, line, bbox) and check
   its center lies inside the physical cell and inside the logical cell bbox;
3. recompute `bbox` as the union of the assigned word bboxes; it must equal
   `LogicalCell.bbox`;
4. recompute `text` with `icpdf.parser.structure::_words_to_text` over the
   assigned words; it must equal `LogicalCell.text`;
5. take the union of all assignment word ids in stored reading order; it must
   equal `LogicalCell.word_ids`;
6. across all logical cells of the table, the assignment word ids must be
   pairwise disjoint and must cover exactly the word universe of §5.6
   (`unassigned_words` excluded);
7. the same physical cell may appear in several assignments, but the word
   subsets must be disjoint. This is the check that a shared physical cell was
   split, not duplicated;
8. check `row_start/row_end` equal the source cell's grid coverage, the
   `logical_column/span` equal the word-bearing run, and `kind` follows the
   `header_rows` rule;
9. recompute `logical_cell_id` from the §5.6 formula and the same
   `(page_number, table_index)`; it must equal the stored id.

This is the independently reconstructable chain the Reviewer requested: the
evidence is per physical cell, per word, and it does not depend on the order in
which the algorithm emitted logical cells.

## 10. Failure strategy (deliverable 6)

### 10.1 Table-level fail-closed

If any candidate is `unresolved`, or any logical-payload check of §11
invariant 21(e) fails:

```text
logical_mapping_status = "unresolved"
logical_mapping_reason = (stable reason codes)
logical_columns = None
logical_boundaries = ()
logical_boundary_detail = ()
column_projection = ()
logical_columns_detail = ()
logical_cells = ()
logical_condition_paths = ()
```

`logical_row_bands` and `logical_boundary_decisions` remain available for
diagnosis, but both are non-authoritative and are not consumed by extraction.
No `demote_condition_path` is retained in `logical_boundary_decisions`, and
`logical_condition_paths` is empty (§6.5). The physical table, S2a visual
fields and candidates remain exactly as before.

### 10.2 Reason codes

Codes are partitioned into five namespaces that never mix. Only namespace L
enters `logical_mapping_reason`.

1. **A-schema** (snapshot loader): `duplicate_key`, `parse_error`,
   `schema_invalid`, `unsupported_version`, `version_mismatch`, `sha_mismatch`.
2. **A-wrapper**: `table_params_snapshot_missing`.
3. **A-audit** (existing read-only tools): `PARAM_SNAPSHOT_HASH`,
   `CONFIG_PARAMS_MISMATCH`, and the other audit codes already in the
   repository.
4. **L** (logical structure): the closed set of 27 codes below.
5. **Diagnostic**: `word_boundary_tie` and the other runtime counters; never a
   reason code.

The L namespace is closed. A code is emitted only through the branch that owns
it, and every branch below names exactly one code.

```text
01 boundary_ambiguous_subrule_ratio
02 boundary_conflicting_sources
03 boundary_data_cell_crossing
04 boundary_no_evidence
05 boundary_condition_subrule
06 boundary_evidence_missing_ref
07 boundary_evidence_mismatch
08 boundary_evidence_stale
09 boundary_evidence_duplicate_ref
10 subrule_run_tie
11 subrule_source_cell_ambiguous
12 mapping_physical_overlap_missing
13 mapping_lattice_index_mismatch
14 mapping_row_band_not_canonical
15 mapping_row_band_overlap
16 mapping_visual_interval_mismatch
17 mapping_row_overlap
18 mapping_word_not_assigned
19 mapping_word_outside_logical_extent
20 mapping_word_partition_mismatch
21 logical_cell_kind_boundary
22 logical_cell_id_collision
23 header_level_tie
24 header_missing_for_canopy
25 header_role_source_invalid
26 region_lattice_inconsistent
27 header_ref_ambiguous
```

The former `boundary_header_gap_too_wide` and
`boundary_partial_rule_not_condition` are **deleted**: neither had a producing
branch. No historical code is renamed. The three
`*_table_params_snapshot_*` names in r14 belong to namespaces 1 and 2 and are
removed from the L list.

**Code-to-branch closure.**

```text
01 boundary_ambiguous_subrule_ratio
   branch: §6.2 row 4; partial rule, ratio in [0.25, 0.50), at least 2 bands
   carrier: decision + table; inv21: (e)(f)

02 boundary_conflicting_sources
   branch: §6.2 last row; keep/demote disagreement after fixed-anchor grouping
   carrier: decision + table; inv21: (e)(f)

03 boundary_data_cell_crossing
   branch: §5.3 + §6.2 crossing row + §8.1; internal candidate with
   supporting_bands > 0 and crossing_bands == supporting_bands
   carrier: decision + table; inv21: (e)(f)

04 boundary_no_evidence
   branch: §6.2 row 6 and row 10 (demote_no_evidence); §8.3 speculative split
   carrier: decision only (excluded from table reason); inv21: (d)

05 boundary_condition_subrule
   branch: §6.2 row 5; non-promoted partial rule with condition_bands >= 1
   carrier: decision only; inv21: (d)

06 boundary_evidence_missing_ref
   branch: §5.3/§9.2 required reference absent or resolving to zero records:
   visual index or segment index out of range, empty required segment list,
   missing subrule field, null header anchor, a declared header ref with zero
   matches (HC-2), no evidence record at all (HC-12), structural ref that does
   not resolve, missing table_bbox/region_extent record, zero region matches,
   no implied_outer record
   carrier: decision + table; inv21: (e)(i)

07 boundary_evidence_mismatch
   branch: §5.4 6.1a stored overlap_fraction outside (0, 1]; §5.3 HC-1b and
   HC-3..HC-9 and HC-11; subrule short_label_ratio mismatch, selected_run_bbox
   not the word union, word not right of x or not in the declared cell;
   label_aligned gutter_ratio recompute beyond 1e-9; structural group span
   beyond tolerance (chain membership); printed_rule role or segment geometry
   contradiction; §5.5 role ref/id resolving to different cells
   carrier: decision + table; inv21: (e)(i)

08 boundary_evidence_stale
   branch: table_bbox page or bbox not exactly equal to the fresh parse;
   region_extent source, boundary_source, page or record content not equal to
   the fresh region
   carrier: decision + table; inv21: (e)

09 boundary_evidence_duplicate_ref
   branch: subrule grid_row/band repeated; structural (grid_row, cell_index,
   edge) triple repeated
   carrier: decision + table; inv21: (e)

10 subrule_run_tie
   branch: §5.3 selected run; two right-side runs in the same physical cell
   whose left edges differ from the minimum by at most 1e-6
   carrier: decision + table; inv21: (f)

11 subrule_source_cell_ambiguous
   branch: §5.3 source cell; x on a shared edge of two DetectedCells, so a band
   has no unique source cell
   carrier: decision + table; inv21: (f)

12 mapping_physical_overlap_missing
   branch: §5.4 6.1a authoritative overlap width zero or negative; §11.6 a
   logical column with no positive physical overlap, or a physical column with
   no positive logical overlap
   carrier: table; inv21: (h)

13 mapping_lattice_index_mismatch
   branch: physical_column not a valid index into the table's one grid.xs;
   physical_left/right not equal to grid.xs[i]/grid.xs[i+1]; LogicalCell
   row_start/row_end not equal to the source cell's grid coverage (§11.12);
   §11.18 accepted-payload logical row/column index outside its lattice
   (bounds only, projection bands excluded); §11.19 fresh grid_ys or n_rows
   different from the artifact
   carrier: table; inv21: (h)
   does not own: band range/shape failures (5.4a), band gap/overlap (5.4b/c),
   logical_column/span equality with the word-bearing run (§11.12.2, A)

14 mapping_row_band_not_canonical
   branch: 5.4a; band_index out of range, row fields not equal to the band,
   signature run not maximal, band order wrong, missing or duplicated band,
   shape outside the lattice, overlap in an empty band, duplicate
   (band_index, physical_column), missing E member, in-band column repeated or
   not ascending
   carrier: table; inv21: (h)

15 mapping_row_band_overlap
   branch: 5.4b uncovered row between two existing bands; 5.4c intersecting
   band row ranges or a fully duplicated band
   carrier: table; inv21: (h)
   note: the code name includes gaps; testing only intersection is a defect

16 mapping_visual_interval_mismatch
   branch: len(visual_boundaries) != visual_columns + 1; visual_column_indices
   out of range, unsorted, repeated, or without positive width overlap; the
   tuple is non-empty iff visual_columns is None violated
   carrier: table; inv21: (h)

17 mapping_row_overlap
   branch: §5.6/§11.12 two logical cells in one table with intersecting row
   ranges
   carrier: table; inv21: (h)

18 mapping_word_not_assigned
   branch: 10.4a word of cell.word_ids missing from that cell's assignment
   union; 10.5a word of the §5.6 universe missing from the table union; empty
   assignment word_ids; §7.3 item 2 non-finite word center
   carrier: table; inv21: (h)

19 mapping_word_outside_logical_extent
   branch: W-1 word center outside the closed outer extent (no tolerance, no
   clamp, no snap); W-2a word center outside the declared physical cell bbox
   (0.8pt inclusive); W-2b word center outside the declared logical cell bbox
   (0.8pt inclusive); 10.5b table union supplies a word outside the extent
   carrier: table; inv21: (h)

20 mapping_word_partition_mismatch
   branch: 10.3 duplicate word id within one LogicalCell's assignments; 10.4b
   assignment union carries a word not in cell.word_ids; 10.5c duplicate word
   id across different LogicalCells
   carrier: table; inv21: (h)

21 logical_cell_kind_boundary
   branch: §5.6 kind rule; word-bearing row range crosses header_rows, or kind
   contradicts the row range
   carrier: table; inv21: (h)

22 logical_cell_id_collision
   branch: §5.6/§7.3 two logical cells under one (page_number, table_index)
   produce the same logical_cell_id
   carrier: table; inv21: (h)

23 header_level_tie
   branch: §5.3 canopy, two same-level header cells touch x within tolerance;
   §8.2 multi-level attribution, top two widths differ by at most 1e-6
   carrier: canopy branch decision + table; §8.2 branch table only;
   inv21: (e)(h)

24 header_missing_for_canopy
   branch: §5.3/§8.2 canopy, at least one side at that level has no header cell
   at all (HC-1a)
   carrier: decision + table; inv21: (f)

25 header_role_source_invalid
   branch: §5.5 role matrix; role_source header_text with both header refs
   null, or role_source outside the four documented values
   carrier: table; inv21: (h)

26 region_lattice_inconsistent
   branch: §5.3/§9.2 region_extent; more than one fresh region has a
   component-id set equal to set(region_components)
   carrier: decision + table; inv21: (i)

27 header_ref_ambiguous
   branch: §5.3/§9.2 header cell resolution (HC-2b); a declared HeaderCellRef
   key (level, source_row, source_column, column) matches more than one
   DetectedHeaderCell
   carrier: decision + table; inv21: (e)(i)
```

**§6.2 branch-to-code map** (no branch without a code, no code without a
branch):

```text
row 1  outer edge                         keep, no code
row 2  full-height printed rule           keep, no code
row 3  promoted subrule                   keep, no code
row 4  ambiguous subrule ratio            boundary_ambiguous_subrule_ratio
row 5  partial rule, condition_bands >= 1 boundary_condition_subrule (demote)
row 6  partial rule, condition_bands == 0 boundary_no_evidence (demote)
row 7  header canopy                      keep, no code; failures are HC-1..HC-12
row 8  label aligned (both thresholds)    keep, no code
row 9  structural (>= 2 body rows)        keep, no code
row 10 none of the above                  boundary_no_evidence (demote)
row 11 all supporting rows crossed        boundary_data_cell_crossing
row 12 sources disagree                   boundary_conflicting_sources
```

A keep row whose evidence validation fails is owned by the §11.8 evidence
codes; a keep row never also produces a demote code.

`word_boundary_tie` is **not** a reason code and is **not** persisted on a
table, a logical cell, a `PhysicalCellAssignment` or a word. It is a
runtime/validator **diagnostic count**: one increment for each `TextWord`
whose center x equals any logical boundary exactly (float equality, no
tolerance), counted at most once per word because the accepted lattice is
sorted and unique. A tie keeps the deterministic left-column assignment of
§7.3, never changes `logical_mapping_status`, and never adds a reason code. An
unresolved table may report no count at all and a resolved table may report a
positive count; the number is reported by the validator alongside the table,
not stored in the parsed artifact. `word_boundary_tie` uses exact float
equality; `subrule_run_tie` uses the `1e-6` left-edge comparison of §5.3. They
are different objects and never share a rule.

### 10.3 No guessing

- Never choose the interpretation that yields a target column count.
- Never choose the interpretation that improves a metric or matches Gold.
- Never fill a missing header from a neighbour.
- Never create a logical column from an empty interval.
- Never downgrade an ambiguity to a demotion to keep the table `resolved`.
- Never treat a Gold `n_columns` fallback as a logical annotation.
- Never infer a `region_extent` from the bbox when the structured extent is
  absent; fail closed instead.

## 11. Invariants and validator checks

Proposed invariants, checked by a new read-only validator (not the S2a
validator):

### 11.0 Check classification (A / L)

Every check below appears exactly once. `L` means the failure is a logical
structure failure: the table becomes unresolved and the code is written to
`logical_mapping_reason`. `A` means the failure is an artifact-integrity or
self-consistency failure: the validator fails hard and no L code is written.
An `L` code is emitted only if §5.3–§9.2 already names it. Stages: C =
construction, V = artifact validation, R = fresh-parse replay, G = frozen
baseline gate.

| check | stage | type | code or result |
| --- | --- | --- | --- |
| 1.1 unresolved iff columns null and payload empty | C+V | A | hard |
| 2.1 boundary arrays equal length; x equal | V | A | hard |
| 2.2 x sorted, unique, inside table bbox | V | A | hard |
| 2.3 every internal boundary has a source | V | A | hard |
| 3.1 logical_columns equals len(boundaries) minus 1 | V | A | hard |
| 4.1 projection length and logical_column sequence | V | A | hard |
| 4.2 every projection has non-empty physical_columns | V | A | hard |
| 4.3 projection left/right equal adjacent boundaries | V | A | hard |
| 5.1 physical_column index and grid.xs coordinates | V | L | mapping_lattice_index_mismatch |
| 5.2 stored overlap is positive | V | L | mapping_physical_overlap_missing |
| 5.3 band_index, band shape, occupancy, band row coverage | V | L | mapping_row_band_not_canonical |
| 5.4a signature run is maximal | V | L | mapping_row_band_not_canonical |
| 5.4b uncovered row between two bands | V | L | mapping_row_band_overlap |
| 5.4c intersecting or duplicate bands | V | L | mapping_row_band_overlap |
| 5.5 in-band columns unique and ascending | V | L | mapping_row_band_not_canonical |
| 5.6 every logical column overlaps at least one physical column | V | L | mapping_physical_overlap_missing |
| 6.1a authoritative width and stored overlap_fraction range | V | L | mapping_physical_overlap_missing or boundary_evidence_mismatch |
| 6.1b stored overlap values do not recompute within 1e-6 | V | A | hard |
| 6.2 overlap_fraction range on every projection record | V | L | boundary_evidence_mismatch |
| 6.3 every physical column overlaps at least one logical column | V | L | mapping_physical_overlap_missing |
| 7.1 visual boundary length equals visual_columns plus 1 | V | L | mapping_visual_interval_mismatch |
| 7.2 visual indices valid, sorted, unique, positive width | V | L | mapping_visual_interval_mismatch |
| 7.3 visual indices empty iff visual_columns is None | V | L | mapping_visual_interval_mismatch |
| 8.1 every declared evidence ref resolves | C+V | L | boundary_evidence_missing_ref |
| 8.2 evidence kind matches declared source | C+V | L | boundary_evidence_mismatch |
| 8.3 header_canopy anchors, sides, labels, boundary_edge | C+V | L | header_level_tie / header_missing_for_canopy / boundary_evidence_mismatch |
| 8.4 subrule source cell, bands, ratio recompute | C+V | L | subrule_source_cell_ambiguous / subrule_run_tie / boundary_evidence_mismatch |
| 8.5 table_bbox equals the fresh DetectedTable | C+V | L | boundary_evidence_stale |
| 8.6 region_extent resolves one region by components | C+V | L | boundary_evidence_missing_ref / region_lattice_inconsistent / boundary_evidence_stale |
| 8.7 structural refs unique, group tolerance, distinct rows | C+V | L | boundary_evidence_duplicate_ref / boundary_evidence_mismatch |
| 8.8 header ref key matches more than one DetectedHeaderCell | C+V | L | header_ref_ambiguous |
| 9.1 anchor membership and tolerance | C+V | A | hard |
| 9.2 group ranges disjoint; no source dropped | C+V | A | hard |
| 9.3 outer x equals bbox edge, not mean | C+V | A | hard |
| 10.1 logical_cells non-empty; every physical ref resolves | V | A | hard |
| 10.2 assignment word_ids non-empty | V | L | mapping_word_not_assigned |
| 10.3 assignment word ids pairwise disjoint | V | L | mapping_word_partition_mismatch |
| 10.4a per-cell union is missing a word | V | L | mapping_word_not_assigned |
| 10.4b per-cell union carries an extra word | V | L | mapping_word_partition_mismatch |
| 10.5a table union is missing a word of §5.6 | V | L | mapping_word_not_assigned |
| 10.5b table union supplies a word outside the extent | V | L | mapping_word_outside_logical_extent |
| 10.5c table union duplicates a word | V | L | mapping_word_partition_mismatch |
| 10.6 fresh parse equals grid builder cell_words capture | R | A | hard |
| 11.1 bbox equals union of assigned word bboxes | V | A | hard |
| 11.2 text equals _words_to_text over those words | V | A | hard |
| 11.3 word_ids is in that reading order | V | A | hard |
| 11.4 cell is not an unmodified copy of a shared physical cell | V | A | hard |
| 12.1 row_start/row_end equal source grid coverage | V | L | mapping_lattice_index_mismatch |
| 12.2 logical_column/span equal the word-bearing run | V | A | hard |
| 12.3 kind follows header_rows | V | L | logical_cell_kind_boundary |
| 12.4 logical_cell_id reproduces from the formula | V | A | hard |
| 12.5 row ranges disjoint within one logical column | V | L | mapping_row_overlap |
| 12.6 logical_cell_id unique within the table | V | L | logical_cell_id_collision |
| 13.1 header refs exist, belong to table, levels in range | V | L | header_role_source_invalid |
| 13.2 role_source is one of the four values | V | L | header_role_source_invalid |
| 13.3 role matrix, sub-rule recipient, no double source | V | L | header_role_source_invalid |
| 13.4 ref and id resolve to the same header cell | V | L | boundary_evidence_mismatch |
| 14.1 grid.xs, grid.ys, cell and S2a fields unchanged | G | A | hard |
| 15.1 candidate ids and counts unchanged | G | A | hard |
| 15.2 candidate logical refs empty on unresolved tables | V | A | hard |
| 16.1 legacy artifact classification | C+V | exempt | unresolved, empty reason |
| 17.1 snapshot schema, hash and version | V | A | schema / audit hard error |
| 18.1 resolved-table lattice audit | V | L | mapping_lattice_index_mismatch |
| 19.1 fresh-parse lattice audit | R | L | mapping_lattice_index_mismatch |
| 20.1 support arithmetic bounds | C+V | A | hard |
| 20.2 all supporting body rows crossed, internal | C+V | L | boundary_data_cell_crossing |
| 20.3 subrule band-count couplings | C+V | A | hard |

Word-membership checks share one code but keep three distinct rules:

| id | stage | type | rule | code |
| --- | --- | --- | --- | --- |
| W-1 | C+V | L | word centre inside the closed outer extent; no tolerance, clamp, snap or widening | mapping_word_outside_logical_extent |
| W-2a | C+V | L | word centre inside its declared physical cell bbox; 0.8pt inclusive | mapping_word_outside_logical_extent |
| W-2b | C+V | L | word centre inside the logical cell bbox; 0.8pt inclusive | mapping_word_outside_logical_extent |

1. `logical_columns is null` iff `logical_mapping_status == "unresolved"`;
   unresolved tables carry no accepted logical payload.
2. `logical_boundaries` and `logical_boundary_detail` have equal length,
   `logical_boundaries[i] == logical_boundary_detail[i].x`, the x tuple is
   sorted and unique, every x is inside the table bbox, and every internal
   boundary has at least one allowed source.
3. `logical_columns == len(logical_boundaries) - 1` when resolved.
4. `column_projection` is the authoritative projection: length equals
   `logical_columns`, `column_projection[i].logical_column == i`, each
   `ColumnProjection` has a non-empty `physical_columns`, and `left` / `right`
   equal `logical_boundaries[i]` / `logical_boundaries[i + 1]`.
5. Every `PhysicalColumnOverlap.physical_column` is a valid index into the
   table's one `grid.xs`; `physical_left == grid.xs[i]` and
   `physical_right == grid.xs[i + 1]`; the overlap is positive. `band_index` is
   in `0 .. len(logical_row_bands) - 1`; the referenced band has a non-empty
   `shape`; `physical_column` is in
   `occupied_columns(logical_row_bands[band_index])`; and
   `grid_row_start` / `grid_row_end` equal that band's fields exactly. Within
   one `(band_index, logical_column)` pair, `physical_column` is unique and
   ascending. For each logical column and band, the emitted physical columns
   are exactly the expected occupancy set `E` of §5.4: an empty band emits
   none, an empty `E` is valid, and a band need not appear in every logical
   column. Every logical column has at least one overlap across all bands;
   otherwise `mapping_physical_overlap_missing`. The `logical_row_bands`
   partition `0 .. n_rows - 1` exactly: a gap is 5.4b and an intersection or
   duplicate band is 5.4c, both `mapping_row_band_overlap`.

5b. `logical_condition_paths` is a bijection with the resolved table's
   `demote_condition_path` decisions: every such decision has exactly one
   record, every record references one such decision, no two records share a
   decision, `condition_path_index` equals the position, `decision_index` is
   strictly ascending, and `partial_rule` equals the unique `subrule_partial`
   in that decision's `evidence` field for field. The record's `row_bands`
   equals that evidence's `condition_bands` and is a subset of the decision's
   `row_bands`. An unresolved table has an empty tuple and no
   `demote_condition_path` decision.
6. `overlap_left`, `overlap_right` and `overlap_fraction` recompute from the
   authoritative interval and physical width within `1e-6`; every logical
   column overlaps at least one physical column and every physical column
   overlaps at least one logical column.
7. On a resolved table, `len(visual_boundaries) == visual_columns + 1` when not
   `None`; every `visual_column_indices` entry is in
   `[0, visual_columns - 1]`, sorted, unique, and has positive width overlap by
   §5.4; the tuple is empty iff `visual_columns is None`.
8. Every kept boundary's evidence resolves per §5.3/§9.2; a missing reference
   is an error, not a warning, and the evidence kind must match the declared
   source. `header_canopy` fails through exactly these branches, one code each:
   HC-1, a required side holds no header cell, is `header_missing_for_canopy`;
   HC-2, a ref whose key matches nothing, is `boundary_evidence_missing_ref`,
   sharing that code with HC-12 under the mutual exclusion below; HC-2b, a ref
   whose key matches more than one cell, is `header_ref_ambiguous`; HC-3 to
   HC-9 and HC-11 — a non-head anchor, a list that is not nearest-first, a
   wrong side, a level contradiction, a bbox outside the table, a label
   failure, a `boundary_edge` position failure, and a wrong evidence kind — are
   `boundary_evidence_mismatch`; HC-10, a same-level geometric tie, is
   `header_level_tie`; a repeated ref inside one declared list is
   `boundary_evidence_duplicate_ref`. HC-10 short-circuits HC-9 for that
   boundary. HC-2 and HC-12 are mutually exclusive: no record means only HC-12
   runs, a record with a zero-match ref means only HC-2 runs, and several
   missing refs on one boundary collapse to one code.
   `subrule_promoted` has one unique source cell per body row or is
   `unresolved`, unique in-band assignments, and a recomputable ratio.
   `table_bbox` matches the fresh `DetectedTable` exactly. `region_extent`
   resolves its region by `region_components` equality before matching the
   record; equal extents alone are never accepted. `structural` refs are unique
   per `(grid_row, cell_index, edge)`, refs for one `(grid_row, edge)` form a
   single group that keeps every ref and satisfies
   `max(edge_xs) - min(edge_xs) <= visual_boundary_tol_pt` with no chain
   membership, and band counting uses distinct `grid_row` values.
9. Candidate decisions obey fixed-anchor grouping: `anchor_x` is a member of
   `source_xs`; every `abs(x - anchor_x) <= visual_boundary_tol_pt`; group
   ranges do not overlap (`max(source_xs) < next_anchor_x`); no source x is
   dropped; an outer decision's x equals the table bbox edge and is not a mean.
10. `LogicalCell.physical_cells` is non-empty; every `PhysicalCellRef` resolves;
    each assignment's `word_ids` is non-empty; assignment word ids are pairwise
    disjoint and their union equals `LogicalCell.word_ids`; across the table
    the union equals the word universe of §5.6, item 5. On a fresh parse,
    `DetectedCell.word_ids` must equal `grid.cell_words[flat_index]` for the
    cell reached by enumerating `grid.cells` with `cell.row == grid_row` and
    non-empty text; the comparison is against the grid builder's capture
    (§7.3), never against a row-local rank.
11. `LogicalCell.bbox` equals the union of its assigned word bboxes;
    `LogicalCell.text` equals `_words_to_text` over those words; `word_ids` is
    in that reading order; it is not an unmodified copy of a shared physical
    cell.
12. `LogicalCell.row_start/row_end` equal the source cell's grid coverage,
    `logical_column/span` equal the word-bearing run, `kind` follows
    `header_rows`, and `logical_cell_id` reproduces from §5.6. Within one
    logical column, logical-cell row ranges are disjoint.
13. Header references exist, belong to the table, and their levels are within
    `header_rows`; `role_source` is one of `header_text`,
    `subrule_short_label`, `heuristic`, `fail_closed`; the role-source/ref
    matrix of §5.5 holds; `subrule_short_label` requires `role = condition` and
    short-label evidence, and the record is exactly the logical column
    immediately right of a kept `subrule_promoted` boundary. No demoted or
    unresolved candidate contributes a role, and no column receives two
    `subrule_short_label` sources.
14. Physical and S2a fields are unchanged: `grid.xs`, `grid.ys`, cell bboxes,
    cell text, `column_index`, `row_span`, `column_span`, `visual_boundaries`,
    `visual_boundary_status`, `visual_columns`, `partial_boundaries`,
    `visual_boundary_evidence`.
15. Candidate ids and counts are unchanged; candidate logical refs are empty on
    unresolved tables.
16. Old run artifacts without logical fields still load and are treated as
    `unresolved`, not as a parse failure. This classification happens **before**
    invariants 18 and 19: an artifact whose `grid_ys` is `()` and whose
    `n_rows` is `0` loads with the legacy defaults, is unresolved, and is never
    audited against a logical lattice. A missing `grid_ys` is not by itself a
    parse failure; a present but malformed `grid_ys` is (§5.7).
17. A replayed `table-params/v1` snapshot reproduces the frozen v1 SHA and
    contains no logical key; a v2 snapshot contains exactly `V2_FIELDS`
    (the 20 v1 names plus the seven logical names). Both are validated from
    raw bytes by `validate_table_params_snapshot`, which loads them itself and
    applies strict root, key, per-field type, bound, version and hash checks
    (§5.8), not only a hash comparison. Duplicate object keys, UTF-8 or JSON
    syntax failure and schema violation carry distinct codes; a non-object root
    or non-object `params` is a schema violation, not a parse failure; and an
    unknown version is refused by the serializer and by the validator. The hash
    is computed over canonical JSON of the parsed document, never over raw
    bytes.
18. **Resolved-table lattice audit (artifact-only).** On a table whose
    `logical_mapping_status` is resolved, `grid_ys` is present with at least
    two coordinates, every coordinate is finite, `n_rows` is at least 1,
    `len(grid_ys) == n_rows + 1`, adjacent pairs are strictly ascending, and
    every logical row index in the accepted payload is inside
    `[0, n_rows - 1]`. The model-level rule is the shared
    `validate_grid_ys` (`icpdf.domain.table::validate_grid_ys`), called by both `Table` and
    `DetectedTable`; this invariant adds the logical-payload row check.
    `rows` may be shorter than `n_rows` because empty grid rows are skipped; a
    validator must never derive `n_rows` from `len(rows)` or require
    `len(rows) == n_rows`. This row-index check does not cover
    `PhysicalColumnOverlap.grid_row_start` or `grid_row_end`: those are
    governed by invariant 5's band rules and use
    `mapping_row_band_not_canonical`, never
    `mapping_lattice_index_mismatch`. This invariant reads persisted fields only and
    applies to resolved tables only; old artifacts were classified unresolved
    in invariant 16 and are out of scope. A violation is
    `mapping_lattice_index_mismatch`.
19. **Fresh-parse lattice audit (separate replay).** A read-only replay that
    re-parses the same PDF must find `tuple(detected.grid_ys) == tuple(grid.ys)`
    and `detected.n_rows == grid.n_rows`, element for element and float for
    float; `grid_ys` is copied verbatim by
    `icpdf.parser.table_detector::detect_tables`, never
    recomputed or normalized. A mismatch is `mapping_lattice_index_mismatch`
    and makes the artifact stale. Invariant 18 cannot detect this because it
    sees only the artifact; invariant 19 cannot run without a fresh parse.
    `grid.xs` and `grid.ys` themselves are never modified by S2b.
20. **Boundary support audit.** For every decision,
    `0 <= crossing_bands <= supporting_bands <= band_count`; `crossing_bands`
    counts only supporting body rows (§5.3), so a header-row crossing or a
    section-like body row removed by §5.3.2 before counting cannot be counted.
    An internal decision is `unresolved` with `boundary_data_cell_crossing` iff
    `supporting_bands > 0` **and** `crossing_bands == supporting_bands`; an
    outer decision is never vetoed. An internal candidate with at least one
    uncrossed supporting row is not unresolved because of crossing, and its
    keep/demote outcome is still determined by §6.2. For non-subrule
    candidates `short_label_bands == condition_bands == 0`; for subrule
    candidates both counts use only the run selected by §5.3.1 for that body
    row, and `short_label_bands + condition_bands <= nonempty_bands`.
    `supported_bands` and `nonempty_bands` have no required ordering;
    `support_ratio = supported_bands / nonempty_bands` may exceed 1.0
    (including for `label_aligned`), is diagnostic, and is `None` iff
    `nonempty_bands == 0`. Every decision satisfies
    `len(row_bands) == support.band_count`, and every section-like body row
    removed in §5.3.2 stays inside `row_bands` and `band_count`.

21. **Reason-code closure.** The following clauses govern every code listed
    in §10.2 and every check classified in §11.0.

    (a) **Namespace separation.** `logical_mapping_reason` contains only the
        closed 27 L codes of §10.2. Namespace A — schema, wrapper and audit
        codes — never enters it, and no A failure sets
        `logical_mapping_status`.

    (b) **Branch totality.** Every L code has at least one producing branch
        named in §5.3–§9.2 and listed in the §10.2 closure table. No code is
        emitted without a branch, and no branch emits a code outside the 27.

    (c) **Branch uniqueness.** One branch emits exactly one code. Where two
        checks inspect the same field, the earlier check in the stated order
        owns the failure and the later check is skipped for that record.

    (d) **Aggregation.** The table reason is the sorted, duplicate-free union
        of unresolved decision codes and failed L-row codes of §11.0.
        `demote_*` codes stay on their decision and never enter
        `logical_mapping_reason`.

    (e) **C+V single reason.** When construction (C) and validation (V)
        inspect the same failure they use the same code and the same producer
        branch. V adds no second code, does not relabel the failure, and does
        not flip the table between resolved and unresolved. Precedence:
        6.1a before 6.1b; HC-10 tie before HC-9 gap geometry; evidence
        resolution before evidence shape.

    (f) **Candidate independence.** Each unresolved candidate contributes its
        own code. A failure of candidate i never suppresses, merges into, or
        relabels a failure of candidate j. Identical codes from several
        candidates collapse only by set union; each per-candidate failure
        remains in the decision records.

    (g) **Partial unresolved.** One unresolved candidate makes the table
        unresolved and clears the logical payload (invariant 1). Resolved
        candidates keep non-authoritative decisions for diagnosis, but no
        projection, boundary, cell or condition-path payload is emitted.

    (h) **Whole-table unresolved.** A table-level audit failure emits one
        reason per failed invariant, not one per failing record. Several
        records failing the same invariant collapse to one code; a different
        failed invariant adds its own code.

    (i) **Early evidence failure.** A boundary whose required evidence fails
        resolution is unresolved with that code. Downstream evidence-shape
        checks for that boundary do not run and add no code. Other boundaries
        continue independently.

    (j) **Legacy exemption.** An invariant 16 artifact is unresolved with an
        empty `logical_mapping_reason` and is exempt from (a)–(i) and from
        invariants 18 and 19.

    The L rows of §11.0 are the closed list for (d) and (e): 5.1–5.6
    (5.4a, 5.4b and 5.4c included), 6.1a, 6.2, 6.3, 7.1–7.3, 8.1–8.8, 10.2,
    10.3, 10.4a, 10.4b, 10.5a, 10.5b, 10.5c, 12.1, 12.3, 12.5, 12.6,
    13.1–13.4, 18.1, 19.1, 20.2, W-1, W-2a and W-2b. The A rows never set
    `logical_mapping_status` and never enter `logical_mapping_reason`.

## 12. Evaluation set and metrics

### 12.1 Sets and exact counts (R2)

**A. Regression set (must not change).**

- Gold v1: `gold/gold_table_set.jsonl`, `annotation_version
  gold-2026-11-06.1`: 46 tables + 19 negatives = 65 items.
- Gold v2: `gold/generalization/gold_table_set.jsonl`,
  `annotation_version gen-2026-11-06.2`: 21 tables + 8 negatives = 29 items.
- Combined positive pool: 67 tables (46 + 21); combined negatives: 27 (19 + 8).
- Phase 1.3 and 1.4 samples, including the six S2a PDFs.
- Checks: S1 physical fields and S2a visual fields zero-diff; candidate ids and
  counts zero-diff; old artifacts load as `unresolved`.

**B. Logical-structure set (new, separately frozen).**

This set is the only source of physical→logical projection and word-partition
ground truth. Gold v2 supplies counts, logical `column_boundaries`, headers and
roles, but it does **not** contain a typed physical→logical projection or a
word partition. The mapping-exact and LogicalCell-exact metrics are therefore
evaluated only on this set, not on Gold v2.

Cases required, each with its own annotation and source PDF SHA:

- cross-column canopy header;
- multi-level header with merged levels;
- merged data cell (`colspan` / `rowspan`);
- blank separator column;
- several physical columns forming one logical field;
- one physical cell referenced by several logical semantics;
- stacked components sharing one logical column inside one region;
- a split physical cell with a per-word assignment.

Known v2 examples can seed this set (CY29FCT520 P04/P05/P06/P08, MICRF103 P03,
DS10CP152 P04/P05/P11), but the set is stored under `gold/s2b/` with its own
manifest, `annotation_version`, `VERSION.json` and SHA. Gold v2 is never edited.

**C. Negative set.**

- boundary with no evidence;
- sub-rule ratio in the ambiguous band;
- missing `HeaderCell` for a canopy boundary;
- physical evidence conflict (data cell or word crossing in every supporting
  band);
- two equally valid logical interpretations;
- incomplete cross-page evidence;
- legacy artifact with no logical fields.

The negative set asserts `logical_mapping_status == "unresolved"` and that
physical/S2a/candidate fields are untouched. It must not assert a made-up
logical count.

**D. Manifest identity and merge checks (R10-N7SET, R11-N7).** The totals in
A–C are reproduced by enumerating the manifests, never by asserting an
arithmetic total. The evaluator checks the three manifests read-only before any
metric runs.

The merged pool is Gold v1 plus Gold v2: those are the two sets combined in A,
and 46 / 19 / 21 / 8 are their enumerated counts. The `gold/s2b/` set is a
separate evaluation set with its own ground truth; §12.1 B deliberately seeds
it from v2 tables, so a v2 item and an s2b item may describe the same physical
table. That reuse is legal only through an explicit `derived_from_item_id`; an
undeclared shared identity fails. `derived_from_item_id` is a provenance
reference, not an `item_id`: it does not join the id namespace and it never
substitutes for the s2b item's own id. A non-derived s2b positive is an
ordinary new identity and collides with neither v1 nor v2, so the declared
v2-to-s2b relation is the only permitted cross-set physical reuse.

Identity of a positive item is `(pdf_sha256, page, table_index)`. `page` is the
manifest's `page` field. `table_index` is the 1-based ordinal in the `-T`
segment of `item_id` (`LM358-P04-T01` is page 4, table 1), and the `page` field
must agree with the `-P` segment. A positive triple is unique inside each
manifest and does not occur in both Gold v1 and Gold v2. A negative item
(`kind: "negative"`) has no table in the manifest and is identified by
`item_id` alone; all 19 + 8 current negatives have that shape.

| Check | Scope | Rule | Code |
| --- | --- | --- | --- |
| within-manifest id | each manifest | every `item_id` occurs exactly once | `eval_manifest_duplicate_item_id` |
| global id | all three manifests | each manifest is read into an `item_id` index; a second occurrence in the same or another manifest is reported with the id, both manifest names and both line numbers; the union-size equality is a redundant post-condition, not the rejection test | `eval_manifest_item_id_collision` |
| polarity | all three | an `item_id` is never positive in one manifest and negative in another | `eval_manifest_polarity_conflict` |
| cross-manifest physical identity | v1 and v2 positives | no `(pdf_sha256, page, table_index)` occurs in both sets; a repeated triple is one physical table counted twice; this version has no exception, and different pages or different table indices are unaffected | `eval_manifest_cross_manifest_identity_collision` |
| within-set physical identity | v1 positives, v2 positives, s2b positives | inside one set, two positives may share a PDF SHA only when their `(page, table_index)` differs; a missing or contradictory `-P`/`-T` segment fails | `eval_manifest_identity_ambiguous` |
| s2b cross-set physical identity | s2b positives against v1 and v2 positives | a non-derived s2b positive shares no `(pdf_sha256, page, table_index)` with any v1 or v2 positive; a derived s2b positive may share only with the single v2 positive it names, and that source is not a v1 positive | `eval_manifest_s2b_identity_collision` |
| derivation | v2 positive to s2b | `derived_from_item_id` resolves uniquely to one v2 positive, never to a negative; the s2b item's `(pdf_sha256, page, table_index)` equals the source's; its own `item_id` differs from the source `item_id`; no two s2b items declare the same source | `eval_manifest_derived_identity_mismatch` |
| counts | each manifest | positive and negative totals equal the enumerated items | `eval_manifest_count_mismatch` |

How the checks are applied:

1. De-duplication is by `item_id`, and the namespace is global across the three
   manifests: an id occurs exactly once in its own manifest and in no other
   manifest. `derived_from_item_id` does not participate in this check. It is a
   separate provenance field, it is not an `item_id`, and it cannot replace or
   excuse the s2b item's own id. An s2b item carries its own id plus an optional
   `derived_from_item_id` that resolves to a v2 item. Detection is by index
   lookup at read time: every manifest is inserted into a map keyed by
   `item_id`, and a second insertion reports the id, both manifest names and
   both line numbers. The union-size equality is a redundant post-condition and
   never the only failure output.
2. A PDF SHA is provenance, not an id. One document supplies up to 20 annotated
   tables in Gold v1, and a document may in principle appear in both Gold sets.
   What may not repeat across Gold v1 and Gold v2 is the positive triple
   `(pdf_sha256, page, table_index)`: the same physical table in both sets would
   be counted twice. Different pages or different table indices under one SHA
   are unrelated identities and are unaffected. This version has no exception
   to the cross-manifest rule; v2-to-s2b reuse is handled by derivation inside
   the s2b manifest, not by relaxing v1 against v2.
3. The current frozen manifests satisfy the stronger rule. v1 has 65 items
   (46 + 19) with 65 unique ids; v2 has 29 (21 + 8) with 29 unique ids; the two
   id sets are disjoint; the two PDF SHA sets are disjoint (three documents
   each, zero overlap); no positive triple repeats inside either set or between
   them; and every positive `page` field agrees with its `-P` segment. These are
   enumerated facts of the files, not assumptions. A future manifest that adds
   a shared document is still checked by the triple rule above.
4. A positive and a negative on the same page are not an identity conflict: the
   negative asserts that its annotated region is not a table and carries no
   `table_index` to collide with.
5. An s2b positive may reference a v2 table only when it carries
   `derived_from_item_id` pointing at a v2 positive item. The reference resolves
   uniquely, never points at a negative, and the derived item's
   `(sha256, page, table_index)` equals the source's exactly. The s2b item keeps
   its own `item_id`, which must differ from the source `item_id`, and at most
   one s2b item may declare a given `derived_from_item_id`, so one physical
   table cannot be counted through several s2b ids. A derived item never
   changes the source PDF identity. A non-derived s2b positive must not share a
   positive triple with any v1 or v2 positive. A derived s2b positive may share
   a triple only with the single v2 positive it names; derivation never targets
   v1, and naming a v2 source cannot excuse a collision with a v1 positive, so
   the exception cannot be used to bypass the v1 boundary. The only permitted
   cross-set physical reuse among the three manifests is the declared
   v2-to-s2b relation; any other shared positive triple fails.
6. Within the s2b set, positives that are not derived follow the same within-set
   rule as v1 and v2: no repeated id and no repeated positive triple. Rule 5
   additionally bars every non-derived collision with v1 or v2.
7. Counts are produced per manifest by enumeration after checks 1–6 pass. The
   hand-written 46 / 19 / 21 / 8 are expected values for the two regression
   manifests; the s2b total is whatever its manifest enumerates and is reported
   separately.
8. Every `item_id` in `gold/s2b/ambiguity_manifest.json` must resolve in its
   declared `gold_set`; overlay entries are not eval items, so they add no
   positive or negative count.
9. The checks are read-only. They open manifests, build index maps and report;
   they never rewrite, reorder or normalize a manifest, and never touch Gold.
10. A failing check stops metric computation for the affected category and is
    reported in the failure list of §12.3. It is never downgraded to a warning.

### 12.2 Gold annotation state and ambiguity overlay (P1-5, N7)

Gold annotation state, Gold ambiguity and algorithm uncertainty are three
separate axes. They are stored separately and are never collapsed into one
status field with a precedence rule.

**Algorithm axis (on the predicted table):**

```text
logical_mapping_status = "resolved" | "unresolved"
```

**Gold annotation axis (on the evaluation manifest, not on the Gold file):**

```text
gold_annotation_state = "typed_decided" | "typed_undecided" | "untyped_legacy"
```

- `typed_decided`: the table carries a non-null typed `logical_columns` in a
  typed (v2) Gold set.
- `typed_undecided`: the table explicitly records `logical_columns: null` in a
  typed (v2) Gold set.
- `untyped_legacy`: the table has no typed logical field at all (all v1
  tables). It is excluded from every logical metric; it remains in detection,
  row, cell-text and visual metrics. The evaluator must not use the
  `gold_table.get("logical_columns", gold_columns)` fallback for S2b logical
  metrics.

**Gold ambiguity axis (on the evaluation manifest, not on the Gold file):**

```text
gold_ambiguity_status = "none" | "open"
```

`open` means an `s2b-ambiguity/v1` overlay entry with the same `item_id`
exists. This axis is orthogonal to the annotation state: a v1 table can be
`untyped_legacy` and still carry an open ambiguity, and a v2 table can be
`typed_decided` while its logical reading is disputed.

**Cross-product and expected algorithm outcome.** Each manifest item occupies
exactly one row; no state overrides another:

| `gold_annotation_state` | `gold_ambiguity_status` | Expected | Reported in |
| --- | --- | --- | --- |
| `typed_decided` | `none` | `resolved` exact match | logical metrics |
| `typed_decided` | `open` | `unresolved` | ambiguity bucket |
| `typed_undecided` | `none` | `unresolved` | undecided bucket |
| `typed_undecided` | `open` | `unresolved` | ambiguity bucket |
| `untyped_legacy` | `none` | not asserted | detection / visual only |
| `untyped_legacy` | `open` | `unresolved` | ambiguity bucket |

Manifest validation is strict and read-only:

- `typed_decided` and `typed_undecided` are assignable only to an `item_id`
  that belongs to a typed (v2) Gold set; the validator rejects either state on
  a v1 item.
- `untyped_legacy` is assignable only to a table whose Gold record has no
  logical field; the validator rejects it for a v2 table that carries
  `logical_columns` or an explicit `null`.
- `gold_ambiguity_status == "open"` requires exactly one overlay entry for that
  `item_id`; `"none"` requires zero entries. Both are checked without editing
  Gold.
- An `open` item is never counted as a resolved exact match, whatever its
  annotation state: it stays out of every exactness denominator and appears in
  the ambiguity bucket together with its predicted
  `logical_mapping_status`.

**Ambiguity overlay.** The five named v1 cases are preserved without editing
Gold:

```text
gold/s2b/ambiguity_manifest.json
  schema_version: "s2b-ambiguity/v1"
  gold_set: "gold-2026-11-06.1"
  annotation_version: "gold-2026-11-06.1"
  items:
    - ambiguity_id: "AMB-COND-BAND-MERGED-01"
      item_id: "ADS1299-P37-T01"
      kind: "merged_vs_split_condition_band"
      status: "open"
      competing_interpretations: ["merged", "split"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/ADS1299-P37-T01.png"
      note: "Gold merges the partial Either-input band while two sibling items split it."
    - ambiguity_id: "AMB-COND-BAND-SPLIT-01"
      item_id: "ADS1299-P70-T01"
      kind: "merged_vs_split_condition_band"
      status: "open"
      competing_interpretations: ["merged", "split"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/ADS1299-P70-T01.png"
      note: "Gold keeps the partial band as a fifth column (split near x=112); frozen for comparability."
    - ambiguity_id: "AMB-COND-BAND-SPLIT-02"
      item_id: "LM358-P04-T01"
      kind: "merged_vs_split_condition_band"
      status: "open"
      competing_interpretations: ["merged", "split"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/LM358-P04-T01.png"
      note: "Gold encodes the partial Either-input band as two condition columns (6); the parser reports 5."
    - ambiguity_id: "AMB-ROLE-UNKNOWN-01"
      item_id: "LM358-P04-T02"
      kind: "headerless_condition_role"
      status: "open"
      competing_interpretations: ["condition", "unknown"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/LM358-P04-T02.png"
      note: "role unknown is correct; do not invent a label"
    - ambiguity_id: "AMB-ROLE-LEADING-01"
      item_id: "ADC12DJ5200-P46-T01"
      kind: "leading_column_role"
      status: "open"
      competing_interpretations: ["value", "symbol"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/ADC12DJ5200-P46-T01.png"
      note: "Gold calls the leading SYSREF bit-field column VALUE; the leading-column heuristic calls it SYMBOL."
```

The overlay validator (read-only) checks that every `item_id` exists in the
declared `gold_set`, that `gold_note_ref` resolves to a non-empty string in the
Gold item, that the referenced `evidence` file exists, and that the same
`item_id` never appears in two entries.

Rules:

- The overlay is read-only with respect to Gold. It records identity, the
  competing interpretations and the existing review note; it never rewrites a
  Gold value.
- No algorithm output may create, resolve or influence an overlay entry.
- Every overlay entry sets `gold_ambiguity_status = "open"` for its `item_id`;
  it does not change that item's `gold_annotation_state`.
- An `open` item is excluded from every exactness denominator and reported in
  the ambiguity bucket; it is never counted as a resolved exact match.
- `LM358-P04-T02` is retained as the case where `role = unknown` is correct;
  the design must not "fix" it by inventing a label.
- An `open` item may be included in the negative/ambiguous detection set.
  The only assertion there is `logical_mapping_status == "unresolved"`; the
  evaluation never requires the algorithm to pick one of the competing Gold
  interpretations, and never asserts a made-up logical column count.
- The overlay is frozen with the S2b set; later additions require a new
  `s2b` evaluation version.

### 12.3 Metrics

| Metric | Definition | Denominator |
| --- | --- | --- |
| LogicalBoundary precision / recall | matched kept boundaries within 2.5pt vs Gold logical `column_boundaries` | predicted / Gold boundaries on `typed_decided` + `none` tables with typed boundaries |
| LogicalColumn exact match | predicted count and ordered intervals equal Gold `column_boundaries` | `gold_annotation_state == "typed_decided"` and `gold_ambiguity_status == "none"` |
| Physical→logical mapping exact match | each logical column's physical column set, `physical_left/right` and row-band overlaps equal the S2b-set annotation | S2b-set cases with an annotated projection, `gold_ambiguity_status == "none"` |
| LogicalCell projection exact match | row range, logical column span, physical cell set and per-cell word partition equal the S2b-set annotation | S2b-set annotated projection cases, `gold_ambiguity_status == "none"` |
| Header provenance coverage | logical columns with a complete, existing header cell chain | labelled logical columns on `typed_decided` + `none` tables |
| Undecided handling | predicted `unresolved` on explicitly undecided tables | `gold_annotation_state == "typed_undecided"` |
| Ambiguous detection recall | predicted `unresolved` on gold-ambiguous cases | `gold_ambiguity_status == "open"` (reported separately) |
| Zero-regression | S1/S2a/candidate fields byte-identical | all regression tables |

The two Gold axes are joined by `item_id`; a metric that quotes only one of
them (for example "on decided tables") is underspecified and is rejected by the
report validator. `untyped_legacy` tables never appear in a logical
denominator, with or without an ambiguity overlay.

Report per-item results and a failure list; never report only a single exact
match. A boundary count match with a wrong physical mapping is a failure, not a
pass. An item with `gold_ambiguity_status == "open"` is never counted as a
resolved exact match.

### 12.4 Anti-overfitting rules

- Freeze the S2b evaluation manifest and SHAs before the first prototype run.
- Fix the proposed parameters before seeing results; any change requires a new
  design review and a new evaluation version.
- Do not add a table to the set because it fixes a metric; do not remove a
  failing table.
- Do not use Gold logical counts as an input to the algorithm, directly or
  indirectly.
- Do not use algorithm output to resolve or modify a Gold ambiguity overlay.

## 13. Staged delivery and review gates

| Stage | Deliverable | Allowed changes | Gate |
| --- | --- | --- | --- |
| S2b-Design | this document | docs only | Reviewer approval required |
| S2b-Schema | models, additive fields, read-only validator, unit tests | no detector integration; no S1/S2a behaviour or Gold change; edits limited to the §5.8 allowlist | Reviewer checks schema, evidence union and snapshot compatibility |
| S2b-Prototype | logical lattice on the standalone S2b set | no pipeline integration; no extraction dependencies | Reviewer checks boundaries, mapping, word partition and failure behavior |
| S2b-Integration | detector/rebuilder integration, full regression, compatibility report | additive wiring only; no physical or S2a change | Reviewer checks zero regression and evidence completeness |

No stage may begin before the previous gate is approved. S2b-Integration is not
authorized by S2a freeze or by this design.

**S2b-Schema edit boundary.** The schema stage may change only the files listed
as allowed in §5.8. In particular it may add the version argument and strict
`V1_FIELDS`/`V2_FIELDS` validation in `config.py`, thread the snapshot version
through `pipeline.py`, add read-only version dispatch to the audit/validate
tools, and add optional logical fields, the additive `TableGrid.cell_words`
capture, and the `grid_ys` / `n_rows` copy.
It may not alter primitive collection, `GRID_TOL`, S2a visual derivation, the
evidence predicates, `grid.xs`/`grid.ys` values or their derivation, physical
cell bbox/text, Candidate IDs, or any Gold file. `grid.ys` is **copied
verbatim** to the additive persisted field `grid_ys` (D6); that copy is not an
alteration of the lattice. Read-only version detection in an existing audit
consumer is a compatibility exception, not permission to change S2a behaviour.
If a required change falls outside the allowlist, the stage stops and returns
to review.

### 13.1 Regression test matrix (T1–T26)

The T1–T26 matrix locked by the batch-5 review is the regression gate for the
schema, prototype and integration stages. r15 revises the eight entries named
by the Reviewer — T7, T13, T16, T20, T21, T22, T25 and T26 — and leaves every
other entry's text unchanged. Status after the r15 merges:

| ID | Title | Status |
| --- | --- | --- |
| T1 | Physical cell split by a promoted boundary | writeable, unchanged |
| T2 | One logical column over two physical columns (demoted sub-rule) | writeable, unchanged |
| T3 | `row_span` 2 inside the body | writeable, unchanged |
| T4 | `row_span` across header and body | writeable, unchanged |
| T5 | Two-level header with a canopy over several columns | writeable, unchanged |
| T6 | Two same-level cells touching x; one side missing | writeable, unchanged |
| T7 | Partial rule with `TA = 25 °C`, ratio below 0.25 | revised below |
| T8 | Full-width section/label merged cell with a body-supported boundary | constructible after §5.3.2; text unchanged, not named for revision |
| T9 | Partial rule with `5 V` or `Data` | writeable, unchanged |
| T10 | Word centre exactly on an internal boundary | writeable, unchanged |
| T11 | Word centre 0.8pt outside the table | writeable, unchanged |
| T12 | Rule table with an empty grid row | writeable, unchanged (D1 merged) |
| T13 | Predicate boundary values | revised below; gutter half OPEN |
| T14 | Artificial corruption | writeable, unchanged (A/L split fixed by §11.0) |
| T15 | Old artifact without logical fields | writeable, unchanged |
| T16 | Physical zero regression before and after S2b-2 | revised below |
| T17 | Same input built twice | writeable, unchanged |
| T18 | Two tables on one page | writeable, unchanged |
| T19 | One physical cell split across three logical cells | writeable, unchanged |
| T20 | Two header cells with the same four-tuple | revised below |
| T21 | Reason closure | revised below |
| T22 | Supporting band crossing | revised below |
| T23 | Promoted role ownership | writeable, unchanged |
| T24 | Selected run consistency | writeable, unchanged (D7 closed) |
| T25 | Empty-row persistence | revised below |
| T26 | Physical cell identity | revised below |

```text
T7 (revised). Partial rule with a condition-like right side below the
ambiguous ratio.

Construction. An internal candidate x carrying exactly one subrule_partial
evidence: 0 < S2a coverage < visual_full_height_coverage, rule_bands
non-empty. In every band the selected right-side run (unique source cell, no
tie) is classified condition_expression, and short_label_ratio is below
logical_subrule_ambiguous_min_ratio (0.25), so condition_bands >= 1.

Expectation. Decision demote_condition_path with reasons exactly
("boundary_condition_subrule",). The decision retains candidate_x, anchor_x,
source_xs, row_bands with one entry per body row (header_rows .. n_rows - 1,
D2), the count fields, the selected source cell ref per band and the selected
run. SubrulePartialEvidence.condition_observations carries exactly one record
per member of condition_bands, each holding the selected run's word ids,
lexical class and relational markers. Exactly one ConditionPathRecord
references the decision (the §6.5 bijection): its row_bands equals
partial_rule.condition_bands and is a subset of the decision's row_bands. S2b
emits no ConditionBand and no ConditionContext. This candidate alone does not
make the table unresolved.

Precondition. If any band has a run tie (two right-side runs whose left edges
differ from the minimum by at most 1e-6), that band emits no
ConditionObservation, does not enter condition_bands, and makes the candidate
unresolved with subrule_run_tie; no ConditionPathRecord may reference that
decision, and T7 does not apply.

Coverage. §5.2 (row_bands, D13 selected run), §5.3 SubrulePartialEvidence,
§5.3.1 run predicate, §6.2 row 5, §6.3 steps 2-6, §6.5, §11.20, §11.21.

Failure semantics. A ConditionPathRecord without its decision or vice versa, an
emitted ConditionBand or ConditionContext, a decision without row_bands, a
ConditionPathRecord whose row_bands copies the decision instead of
condition_bands, boundary_no_evidence instead of boundary_condition_subrule, or
a silently resolved tie all fail.
```

```text
T13 (revised). Predicate boundary values.

Construction.
Crossing side, strict straddle bbox[0] < x < bbox[2]:
word A starts right of x and ends at x + 0.1 (does not cross);
word B starts at x - 0.1 and ends at x + 0.1 (crosses);
word C ends exactly at x (does not cross).
Rule side: one row whose segment covers only part of the row, and one row
whose segment covers all of it.
Section side: a body cell that spans the table horizontally and whose left
edge is exactly grid.bbox[0] + visual_boundary_tol_pt in one case, and beyond
that value in another.
Gutter side: adjacent-word gaps 7.9, 8.0 and 8.1 against cell_gap_pt = 8.0.

Expectation. A not crossing, B crossing, C not crossing; no margin of any
size, and the former 1.9/2.1 construction is withdrawn. A partially covered
row has rule_at true and row_coverage < 1.0; neither gates printed_rule, which
uses only the S2a overall coverage (§5.3.1 item 3). The D16 predicate includes
the tolerance: a cell edge exactly at grid.bbox[0] + visual_boundary_tol_pt is
section-like and one beyond it is not. For the run predicate, gaps 7.9 and 8.0
stay in one run and 8.1 starts a new run, because the split is strict.

Coverage. §5.3.1 items 1-3; §5.3.2; §11.20.

Failure semantics. A or C counted as crossing, B not counted, any margin,
row_coverage used to gate printed_rule, a D16 boundary that excludes the exact
tolerance, or 8.0 treated as a new run all fail.

OPEN (gutter half). r14 and r15 define no geometric gutter predicate. §5.3.1
says a gutter row cannot be a crossing row because the gutter predicate
requires that no word crosses x, while §9.2 (LabelAlignedEvidence ratio) says
a word crossing x in a gutter row is not an evidence error and only removes
that row's support. The two statements cannot both hold, and neither defines
gutter geometry. Until §14 item 23 is ruled, only the 7.9/8.0/8.1 run vectors
are normative and the gutter half of T13 is not writeable.
```

```text
T16 (revised). Physical zero regression before and after S2b-2.

Construction. Same PDF and same TableParams. Run A is the frozen pre-S2b-2
build; run B is the post-S2b-2 build; neither the YAML config nor the params
change.

Expectation. Compare canonical values, never raw JSON bytes:
1. elementwise float equality of grid.xs and grid.ys;
2. equality of cell bbox, cell text, column_index, row_span, column_span,
   candidate ids and the S2a visual fields listed in §11 invariant 14, after
   canonical serialization with json.dumps(value, ensure_ascii=False,
   sort_keys=True, separators=(",", ":")) and allow_nan=False;
3. equality of the named hashes: parser_config_sha256 (the YAML config hash,
   which is unchanged) and table_params_sha256 (the canonical snapshot hash of
   §5.8).

This design defines no table-level evidence hash, so a test must not invent an
unnamed one. If S2b-2 later adds one, the test names it and it stays
auxiliary, never a substitute for items 1 and 2.

Coverage. §5.8 (canonical JSON and the two named hashes); §11 invariant 14 and
§11.0 row 14.1; §13.

Failure semantics. Any changed physical or S2a value fails. Byte comparison of
raw JSON, or equality of a hash not named above, is evidence of neither
regression nor equality.
```

```text
T20 (revised). Two header cells with the same identity key.

Construction. Two DetectedHeaderCell records with identical
(level, source_row, source_column, column); a HeaderCellRef declared on a
canopy edge resolves that key.

Expectation. Identity resolution is step one of the two-step model. More than
one match yields header_ref_ambiguous (L code 27) and the candidate and table
are unresolved; neither cell is selected and no content check is attempted.
The other outcomes keep their own codes and never mix: zero matches is
boundary_evidence_missing_ref; one match failing its text, bbox or level check
is boundary_evidence_mismatch; a ref repeated inside one list is
boundary_evidence_duplicate_ref; two same-level cells geometrically touching x
within visual_boundary_tol_pt is header_level_tie; a side with no cell at that
level at all is header_missing_for_canopy.

Coverage. §5.3 header_canopy row; §9.2 header_cell_refs (steps 1-2); §10.2
code 27; §11.0 rows 8.3 and 8.8; §11 invariant 8.

Failure semantics. Silent first match, boundary_evidence_mismatch or
header_level_tie emitted for a multi-match, or header_ref_ambiguous emitted
for a zero or single match all fail.
```

```text
T21 (revised). Reason closure.

Construction. Enumerate every branch of §6.2, every evidence branch of
§5.3-§9.2, and every code of §10.2.

Expectation. Five namespaces stay separate: A-schema, A-wrapper, A-audit, L
(27 codes) and Diagnostic. logical_mapping_reason contains L codes only, and
the L set is closed at exactly 27. Each L code has at least one producing
branch, every L-producing branch emits exactly one L code, and keep branches
emit none (§10.2 closure table, §11.21 (b) and (c)). header_ref_ambiguous is
reachable from HC-2b. The deleted codes
boundary_header_gap_too_wide and boundary_partial_rule_not_condition are
absent. word_boundary_tie is a diagnostic count, never a reason code and never
persisted. Schema, wrapper and audit codes never enter logical_mapping_reason
and never set logical_mapping_status.

Coverage. §10.2 (namespaces, the 27-code list, closure and §6.2 map); §11.0;
§11.21.

Failure semantics. Any code without a branch, any branch without a code, a
26-code set, a deleted code, a diagnostic code in the reason tuple, or an A
code in the reason tuple fails.
```

```text
T22 (revised). Supporting band crossing.

Construction. Case 1: exactly two supporting body rows, one crossed by a body
data cell or word. Case 2: the same two rows, both crossed. Case 3: a
section-like body row carrying a full-width merged cell and a full-height rule
at x, with the other body rows supporting x.

Expectation. Case 1 removes only the crossed row's support; with
supporting_bands = 2 and crossing_bands = 1 the candidate is not unresolved
because of crossing and its keep or demote outcome is still decided by §6.2.
Case 2 gives supporting_bands = 2, crossing_bands = 2 and unresolved with
boundary_data_cell_crossing. Case 3 removes the section-like row from
rule_bands, gutter_bands and the structural source before counting, so it is
neither supporting nor crossing and its crossing is diagnostic only. Counting
is per row, never per word or per cell, and every decision satisfies
0 <= crossing_bands <= supporting_bands <= band_count. Header rows are never
counted. Every body row, including the section-like one, stays in row_bands
and band_count.

Coverage. §5.2 supporting and crossed rows; §5.3.2; §6.2 crossing row and D14
objects; §8.1; §11.20.

Failure semantics. A single crossed row making the candidate unresolved,
counting words or cells instead of rows, a header or section-like row entering
the denominator, or an all-crossed candidate other than
boundary_data_cell_crossing all fail.
```

```text
T25 (revised). Empty-row persistence.

Construction. A ruled table whose grid has a row with no non-empty text cell,
so len(rows) < n_rows.

Expectation. grid.ys (n_rows + 1 coordinates), n_rows and header_rows are
persisted; len(rows) < n_rows is legal and is never used to derive n_rows. The
empty row keeps its place in 0 .. n_rows - 1, stays in band_count, and takes
part in a D1 band whose signature is the empty tuple (); it may share that
band with an adjacent row of the same signature. The projection emits no
PhysicalColumnOverlap for an empty band, but the band itself exists. Logical
payload row indices stay inside 0 .. n_rows - 1, and len(row_bands) ==
band_count includes the empty row.

Coverage. §5.4 bands and occupancy; §5.7 additive fields; §7.3 D6; §11.0
rows 5.3-5.5 and 18.1; §11 invariants 18 and 20.

Failure semantics. Deriving n_rows from len(rows), dropping or duplicating a
band, a wrong band row range, or a gap or overlap between consecutive bands
fail, with mapping_lattice_index_mismatch, mapping_row_band_not_canonical and
mapping_row_band_overlap respectively.
```

```text
T26 (revised). Physical cell identity.

Construction. (a) A persisted cell preceded in its row by an empty grid cell,
so the row-local index and the flat TableGrid.cells index differ. (b) A grid
cell whose stripped text is empty but which carries words.

Expectation. (a) PhysicalCellRef.cell_index is the row-local index inside
DetectedRow.cells, not the flat index;
flat = offset(r) + j + skipped_before(r, j) resolves the intended GridCell;
column_index matches that cell; cell_id is None at parser level and is filled
after rebuild. (b) The cell is not persisted as a DetectedCell by
detect_tables, its words remain in the §5.6 universe (they are assigned to
grid.cells), no logical cell can carry them, and the table fails closed as
unresolved with mapping_word_not_assigned (code 18; §11.0 row 10.5a, a word of
the §5.6 universe missing from the table union). No empty cell is invented and
no word is silently dropped.

Coverage. §5.6 D5 (two index spaces and the conversion), §5.6 item 5 (word
universe), §5.7, §7.3, §11.0 rows 10.2/10.4a/10.5a, §10.2 code 18.

Failure semantics. Writing the flat index into cell_index, resolving a
different cell, inventing an empty cell, dropping the words, or emitting any
code other than mapping_word_not_assigned for (b) fails.

OPEN (code choice). The batch-5 review suggested
mapping_word_partition_mismatch for (b). §10.2 assigns a missing universe word
to mapping_word_not_assigned (18) and duplicates or extras to
mapping_word_partition_mismatch (20), so using 20 here would contradict the
code-to-branch closure and T21. r15 uses 18; §14 item 24 asks the Reviewer to
confirm this reading.
```

## 14. Open decisions for Reviewer

1. Approve the proposed logical parameters and the version-dispatched
   `table-params/v2` snapshot, including the frozen v1 field list and the
   replay rules in §5.8.
2. Approve retaining `logical_boundary_decisions` as a non-authoritative
   diagnostic on unresolved tables (accepted payload remains empty).
3. Confirm that a fully ruled blank column is kept as a `printed_rule` logical
   column with `role = "unknown"`, rather than treated as an unresolved case.
4. Confirm that section-band semantics and condition bands remain out of S2b;
   `demote_condition_path` is only a path label for S2c and emits no band.
5. Confirm that header-canopy boundaries may add logical x positions where
   `grid.xs` has no boundary, as long as the physical grid is untouched.
6. Confirm the location/name of the new S2b evaluation set (`gold/s2b/`), its
   ambiguity overlay, and its freeze procedure.
7. Confirm the role provenance alignment: `role_source` uses the existing
   `header_text` / `heuristic` / `fail_closed` values plus the approved S2
   `subrule_short_label`, `role_evidence` carries a stable code,
   `role_header_cell_id` carries the domain `HeaderCell.header_cell_id`, and a
   promoted boundary confers `subrule_short_label` only on the logical column
   immediately to its right (§5.5).
8. Confirm the two Gold axes in §12.2 (`gold_annotation_state`,
   `gold_ambiguity_status`) and that all v1 tables are `untyped_legacy` for
   logical metrics, with the existing `n_columns` fallback never used as a
   logical annotation.
9. Confirm that `PhysicalColumnOverlap` is table-global (one `grid.xs` per
   table) and that cross-table aggregation is out of scope for S2b.
10. Approve the directed `HeaderCanopyEvidence` record (§5.3), including
    `boundary_edge`, the two anchor refs and the multi-cell membership rules.
11. Approve the per-band `SubruleLabelAssignment` record and the ratio formula
    in §6.3 as the only promotion evidence.
12. Approve `TableBBoxEvidence`/`RegionExtentEvidence` being validated against
    a fresh parse (`boundary_evidence_stale`), and the indexed
    `implied_outer` encoding in §5.3.
13. Approve fixed-anchor candidate grouping (§6.1) and the retained
    `candidate_x` / `anchor_x` / `source_xs` fields that make grouping
    auditable without re-grouping.
14. Approve the lexical classes and the frozen unit lexicon in §6.3.1, and the
    rule that a `field_name` or `prose` right side never becomes
    `condition_path` (§6.5).
15. Approve the `LogicalCell` decomposition, bbox, text, deterministic ID and
    kind rules in §5.6/§9.3, including the canonical word universe.
16. Approve strict snapshot schema validation (`table_params_snapshot_schema_invalid`,
    `table_params_snapshot_version_mismatch`) and the §13 edit boundary for
    S2b-Schema.
17. Confirm that the closed `x` containment for the sub-rule source cell is a
    deliberate fail-closed rule (§5.3/§6.3), so an `x` on a shared cell edge
    yields `subrule_source_cell_ambiguous` rather than a silent tie-break.
18. Approve region identity by `region_components` equality (§5.3/§9.2),
    including `region_lattice_inconsistent` for multiple matches.
19. Approve the marker-first lexical order, the longest-match tokenization rule
    (including `..` and the multi-character operators), the operand grammar, the
    frozen `LOGICAL_SYMBOL_TOKENS` set and the unary `±` exception in §6.3.1.
20. Approve the structural source-group rule (§5.3/§9.2/§11): refs are unique
    per `(grid_row, cell_index, edge)`, refs for one `(grid_row, edge)` form one
    group that keeps every ref and satisfies
    `max(edge_xs) - min(edge_xs) <= visual_boundary_tol_pt`, and bands are
    counted by distinct `grid_row`.
21. Approve the conservative non-recognition policy in §6.3.1: a run that
    carries an operator but matches no production is `unclassified` and
    demotes; no lexical outcome is `unresolved` and no unknown symbol or
    connector is guessed.
22. Confirm the identity rule of §12.1 D, including four constraints on the
    v2-to-s2b exception and its closure boundary. First,
    `derived_from_item_id` resolves uniquely to a v2 positive item and never
    points at a negative. Second, the derived s2b item and its source carry
    fully equal `(pdf_sha256, page, table_index)`. Third, a derived item does
    not change the source PDF identity, and one physical table is never counted
    through multiple s2b `item_id`s: at most one s2b item may declare a given
    `derived_from_item_id`, so the exception cannot become a bypass of identity
    uniqueness. Fourth, a non-derived s2b positive shares no positive triple
    with any v1 or v2 positive; naming a v2 source never excuses a v1
    collision. Thus the declared v2-to-s2b relation is the only permitted
    cross-set physical reuse. Outside that exception, the merged pool is v1
    union v2, an s2b item keeps its own `item_id` (which must differ from its
    v2 source), and an undeclared shared `(sha256, page, table_index)` fails.
    Strict disjointness across all three manifests would forbid the v2 seeding
    that §12.1 B allows.
23. Resolve the gutter predicate. Neither r14 nor r15 defines the geometry of a
    body gutter at x, yet `gutter_bands`, `label_aligned`, `gutter_ratio` and
    the denominators of §6.2 depend on one. Two statements also conflict:
    §5.3.1 says a gutter row cannot be a crossing row because the gutter
    predicate requires that no word crosses x, while §9.2 says a word crossing
    x in a gutter row is not an evidence error and only removes that row's
    support. The ruling must name the exact geometry (which cells and words
    are consulted, the tolerance, and whether a body data cell may overlap the
    gutter) and choose which of the two statements governs. Until then the
    gutter half of T13 and every gutter-based `label_aligned` construction
    remain OPEN.
24. Confirm the fail-closed code for T26(b), a grid cell with words but empty
    stripped text: `mapping_word_not_assigned` (18) as derived from §5.6 item
    5 and §11.0 row 10.5a, or `mapping_word_partition_mismatch` (20) as
    suggested in the batch-5 review. Code 20 owns duplicates and extras
    (§10.2), so adopting it here would require reopening the code closure and
    T21.

## 15. Acceptance checklist for the design gate

- [ ] Six deliverables are answered: data model, mapping, merged cells,
      boundary decisions, evidence chain, failure strategy.
- [ ] R1–R7 are answered with repository paths and line references.
- [ ] P0-1..P0-4 and P1-1..P1-5 are closed in the document.
- [ ] N1 is closed: `HeaderCanopyEvidence` is directed, names both anchors,
      and an independent auditor can decide the boundary from the record and
      the header cells alone.
- [ ] N2 is closed: `SubrulePromotedEvidence` carries per-band, per-cell and
      per-word assignments, and `short_label_ratio` is recomputable from them.
- [ ] N3 is closed: `TableBBoxEvidence` and `RegionExtentEvidence` are checked
      against a fresh parse, and the `implied_outer` values are structurally
      encoded.
- [ ] N4 is closed: candidate grouping uses a fixed anchor and retains every
      source x.
- [ ] N5 is closed: `condition_path` requires an explicit condition marker and
      the ratio formula is exact.
- [ ] N6 is closed: `LogicalCell` bbox, text, id, row-span and word universe
      are reproducible without algorithm-specific knowledge.
- [ ] N7 is closed: `gold_annotation_state` and `gold_ambiguity_status` are
      independent axes joined by `item_id`.
- [ ] N8 is closed: v1/v2 snapshots are schema-validated, and the S2b-Schema
      edit boundary is explicit.
- [ ] S1–S3 are closed: role-ref contradiction, projection/visual geometry and
      structural/tie-break edge cases.
- [ ] r4/N2 is closed: the closed-interval source-cell rule and the
      `rule_bands`-only denominator are both stated as intentional.
- [ ] r4/N3 is closed: `region_extent` resolves its region by
      `region_components` equality before validating the record.
- [ ] r4/N5 is closed: the relational marker is tested before every content
      class, and tokenization plus the unary `±` exception are explicit.
- [ ] r4/S3 is closed: structural refs are unique per
      `(grid_row, cell_index, edge)`, agreeing refs form one group, and bands
      are counted by distinct `grid_row`.
- [ ] r5/N5-1 is closed: tokenization is a longest-match scan over frozen token
      classes, and `..` plus `>=`/`<=` are explicit separators.
- [ ] r5/N5-2 is closed: the operand grammar separates `operand`,
      `value_phrase` and `value_bearing`, with worked examples for `A=B`,
      `A>=B`, `VCC=5V`, `5V–10V` and `5..10 V`.
- [ ] r5/N5-3 is closed: `LOGICAL_SYMBOL_TOKENS` is a closed six-token set and
      `VIN`, `TEMP`, `CLK` are excluded by name.
- [ ] r5/S3-span is closed: a structural source group is bounded by
      `max(edge_xs) - min(edge_xs) <= visual_boundary_tol_pt`, never by
      consecutive-neighbour agreement.
- [ ] r6/N6-text is closed: §5.6 item 3 states the exact `_words_to_text`
      algorithm, including the running-mean update order, the `median`/`8.0`
      fallback, tie order, joiners and the empty-input result.
- [ ] r6/N5-token is closed: §6.3.1 carries normative tokenizer test vectors
      and the three numeric content classes are disjoint.
- [ ] r6/N7-N8 is closed: §16 records the full-document comparison with the
      r3 text the Reviewer already accepted for N7 and N8.
- [ ] r7/N5-hyphen is closed: the word-run hyphen rule is asymmetric (the left
      neighbour is never a digit), and `CLK-1`, `CLK-ABC`, `CLK-`, `5-10`,
      `5V-10V` and `5 V -10 V` are normative vectors.
- [ ] r7/N5-mult is closed: multipliers count only as standalone tokens, and
      `10kΩ` is `10`, `kΩ` with class `value_with_unit`.
- [ ] r7/N6-verify is closed: §5.6 item 3 is delivered in full and matches
      `icpdf.parser.structure::_words_to_text` operation for operation.
- [ ] r7/N7-N8 is closed: §16 records both input digests, unique heading
      anchors, excerpt sizes and digests, exit codes and the 17-invariant
      result.
- [ ] r8/R8-CLASS is closed: content classes are run-level, `identifier` is
      single-token, `5V-10V` is `unclassified` and `V-10V` alone is
      `identifier`, and `identifier`'s downstream effect is tabulated.
- [ ] r8/R8-LOSS is closed: §5.6 item 3 and §16.3 are carried both as readable
      text and, out-of-band, as base64 with SHA-256 (§16.6), so the reviewed
      bytes can be rebuilt.
- [ ] r8/R8-ANCHOR is closed: §16 matches whole heading lines with `$0==s`, and
      a missing or duplicated anchor aborts with exit 3.
- [ ] r9/R9-KIND is closed: `kind` is `header` iff `row_end ≤ header_rows - 1`,
      `data` iff `row_start ≥ header_rows`, and a crossing cell is
      `logical_cell_kind_boundary` with the table unresolved; six boundary
      rows are normative.
- [ ] r9/R9-WORD is closed: the no-logical-cell rule is stated for a physical
      cell whose words land in no logical column.
- [ ] r9/R9-LOSS2 is closed: §5.6 and §16 are delivered out-of-band as base64
      with SHA-256, and §16.6 explains why §16 cannot carry itself.
- [ ] r9/R9-ORDER is closed: the script rejects an end heading that precedes
      its start heading with exit 4.
- [ ] r11/R11-N7-1 is closed: §12.1 D makes
      `(pdf_sha256, page, table_index)` unique across Gold v1 and Gold v2
      positives, with `eval_manifest_cross_manifest_identity_collision` and no
      exception in this version.
- [ ] r11/R11-N7-2 is closed: `item_id` is globally unique across all three
      manifests, and `derived_from_item_id` is a separate provenance reference
      that neither joins the id namespace nor substitutes for the s2b item's
      own id, which must differ from its v2 source. A non-derived s2b positive
      shares no positive triple with v1 or v2; a derived one shares only with
      its unique declared v2 source. Collisions are reported from the id and
      identity indexes with both locations, not only as a set-size mismatch.
- [ ] r11/R11-N8LOAD-1 is closed: `validate_table_params_snapshot` takes raw
      bytes, calls `load_table_params_snapshot` itself, and maps duplicate key,
      UTF-8/JSON parse error and schema violation to three distinct codes; no
      entry point accepts a `dict` or a pre-loaded object. A non-object JSON
      root or a non-object `params` member returns
      `table_params_snapshot_schema_invalid`, never `parse_error`.
- [ ] r11/R11-N8LOAD-2 is closed: §5.8 states that the hash is canonical JSON
      over the parsed document, not raw bytes, and that stored integer/float
      types are not coerced before hashing.
- [ ] r11/R11-22 is closed: §14 item 22 constrains the derivation to a unique
      v2 positive source, fully equal identities, and at most one s2b id per
      physical table, and bars a non-derived s2b positive from sharing identity
      with any v1 or v2 positive.
- [ ] r10/R10-N8VER is closed: §5.8 dispatches v1/v2 with two explicit branches
      and raises for any other version; `table_params_sha256` shares that
      dispatch.
- [ ] r10/R10-N8FIELDS is closed: §5.8 tabulates the 20 v1 names as declared in
      `icpdf.parser.config::V1_FIELDS`, and the per-field rules reject
      `true`/`false` for an
      integer field.
- [ ] r15/D1-D3 are closed: the projection bands and `BandObservation` carrier
      of §5.4 are one partition, `row_bands` is defined once in §5.2, and the
      four predicates of §5.3.1 are the only normative geometry.
- [ ] r15/D7 is closed: §5.2, §5.3 and §6.3 states one
      `run_left - m <= 1e-6` tie rule, compared against `m` only and never
      chained, and any tie makes the whole candidate unresolved.
- [ ] r15/D10-D12 are closed: the L set is exactly 27 codes, the five
      namespaces never mix, the branch-to-code map is total in both directions,
      and A failures never set logical status.
- [ ] r15/D14 is closed: `BoundarySupport`, the projection bands and the
      evidence records stay distinct; §6.2 names every keep threshold and
      denominator; a failed `label_aligned` threshold demotes with
      `boundary_no_evidence` and retains its support.
- [ ] r15/D15 is closed: header references resolve in two ordered steps, with
      `header_ref_ambiguous` for more than one identity match.
- [ ] r15/D16 is closed: the geometric section-like predicate of §5.3.2 is
      used by §5.2, §6.2, §8.1 and invariant 20, and section-like rows stay in
      `band_count` and `row_bands`.
- [ ] r15/T matrix is delivered: §13.1 revises T7, T13, T16, T20, T21, T22,
      T25 and T26, and records the status of every other entry.
- [ ] r15/OPEN items are settled or accepted as open: the gutter predicate and
      the §5.3.1/§9.2 conflict (§14 item 23) and the T26 code choice (§14 item
      24).
- [ ] Hard constraints in §4 are accepted.
- [ ] Proposed parameters and the v1/v2 snapshot dispatch are approved or
      amended.
- [ ] S2b evaluation set, ambiguity overlay, metrics and anti-overfitting rules
      are approved.
- [ ] No implementation is authorized until this design gate passes.

## 16. Full-document verification of N7/N8 and §11 (r9)

The r5 review correctly noted that a no-touch diff proves only that a section
was not edited, the r6 review added that this section's own script is audit
evidence, and the r7 and r8 reviews added that the script, the §5.6 pseudocode
and this section itself must survive delivery without character loss. This
section therefore records both inputs' identity, the heading anchors, their
uniqueness and their required order, extracted line and byte counts, excerpt
digests, exit codes, an itemized result for §11, and the delivery channel for
the two sections whose bytes the text renderer damaged.

### 16.1 Inputs

| Input | Identity |
| --- | --- |
| r3 text, the N7/N8 reference | `tmp/PHASE1_4_S2B_DESIGN_r3.md`; 2,175 lines, 109,767 bytes; SHA-256 `974e49749d1b79f00a9d2f07179caefa2895328b3ceb63283b3e136946fe7811` |
| r9 text, this document | working tree `docs/PHASE1_4_S2B_DESIGN.md`; digest reported in the delivery message |
| comparison script | `tmp/verify_sections.sh`; 93 lines, 2,432 bytes; SHA-256 `129c84174f45889c89c8f85207344ff701f4eec4a2751a2e60e9882237246825`; byte-exact copy in the delivery message (§16.6) |
| §5.6 pseudocode | the fenced block in §5.6 item 3; 16 lines, 710 bytes; SHA-256 `dc3d986339dc377dac1acf6ec9d694043ba58527febb587b2aeca87c3c7825d1`; byte-exact copy in the delivery message (§16.6) |

The r3 text was never committed: it existed only as an uncommitted working-tree
revision of this file on top of `6f3e58d`, and it was archived verbatim before
the r4 edits began. The archive, not a git object, is the reference.

A document cannot contain its own SHA-256: writing the digest into the file
changes the file, so any recorded value would already be stale. The r9 digest is
therefore reported in the delivery message and is reproducible from the file:

```text
sha256sum docs/PHASE1_4_S2B_DESIGN.md
```

The same holds for the delta artifact; its digest is reported alongside it. The
two artifacts in §16.6 are not this document, so their digests can and do appear
here.

### 16.2 Method

Sections are delimited by headings, never by line numbers. An anchor is a
**whole heading line**, compared with `$0==s` (exact equality), and the extractor
stops at the first later line with `$0==e`.

Exact equality replaced the earlier prefix test `index($0,s)==1`, which the r7
review correctly rejected: with `s = "## 12."`, a line `## 12.2 Gold annotation`
matches at column 0, so a document could satisfy a prefix anchor without
containing the intended section, and prefix uniqueness says nothing about
section uniqueness. Newlines cannot occur inside a line, so `$0==s` also cannot
be satisfied by a heading that merely starts the same way.

Before extracting, both the start and the end heading must occur exactly once
in each input, and the end heading must occur **after** the start heading;
otherwise the script aborts, with exit 3 for a missing or duplicated anchor and
exit 4 for an invalid order. The failure modes covered are:

- missing anchor: the exact count is 0. Removing `## 12. Evaluation set and
  metrics` from a copy of the r3 archive produced
  `heading not unique (0 occurrences)` and exit 3;
- duplicated title: the exact count is 2 or more, and the run aborts the same
  way;
- reversed order: moving `## 11. Invariants and validator checks` to the end
  of a copy of this document produced `heading order invalid` and exit 4,
  because its end anchor then precedes it. Without this check the extractor
  would have emitted an empty or nonsensical range instead of failing.

The full anchors are therefore spelled out, including the trailing parenthetical
of §5.8 and the inline code of §5.9, so no anchor can be satisfied by a
different heading.

### 16.3 Script

```sh
#!/bin/sh
# Compare heading-delimited excerpts of the r3 archive and the current draft.
# Exact Markdown heading match: a heading is a whole line, compared with ==.
# Usage: sh verify_sections.sh <r3.md> <current.md>
# Exit 0: every anchor was unique, in order, and every comparison ran.
# Exit 2: temporary directory failed. Exit 3: an anchor was missing/duplicated.
# Exit 4: an end heading does not occur after its start heading.
set -u

r3=$1
cur=$2
work=$(mktemp -d) || exit 2
trap 'rm -rf "$work"' EXIT

count_exact() {
  awk -v h="$1" '$0==h{c++} END{print c+0}' "$2"
}

line_of() {
  awk -v h="$1" '$0==h{print NR; exit}' "$2"
}

require_unique() {
  n=$(count_exact "$1" "$2")
  if [ "$n" -ne 1 ]; then
    printf 'heading not unique (%s occurrences): %s in %s\n' "$n" "$1" "$2" >&2
    exit 3
  fi
}

extract() {
  awk -v s="$1" -v e="$2" '
    $0==s {on=1}
    on    {print}
    on && $0==e {exit}
  ' "$3"
}

check() {
  label=$1
  start=$2
  end=$3
  require_unique "$start" "$r3"
  require_unique "$start" "$cur"
  require_unique "$end"   "$r3"
  require_unique "$end"   "$cur"
  s3=$(line_of "$start" "$r3")
  e3=$(line_of "$end" "$r3")
  sc=$(line_of "$start" "$cur")
  ec=$(line_of "$end" "$cur")
  if [ "$e3" -le "$s3" ] || [ "$ec" -le "$sc" ]; then
    printf 'heading order invalid: end %s does not follow start %s\n' \
      "$end" "$start" >&2
    exit 4
  fi
  extract "$start" "$end" "$r3"  > "$work/a.txt"
  extract "$start" "$end" "$cur" > "$work/b.txt"
  if diff -q "$work/a.txt" "$work/b.txt" >/dev/null; then
    rc=0
  else
    rc=1
  fi
  printf '%s lines %s/%s bytes %s/%s sha %s/%s rc=%s\n' \
    "$label" \
    "$(wc -l < "$work/a.txt" | tr -d ' ')" \
    "$(wc -l < "$work/b.txt" | tr -d ' ')" \
    "$(wc -c < "$work/a.txt" | tr -d ' ')" \
    "$(wc -c < "$work/b.txt" | tr -d ' ')" \
    "$(sha256sum < "$work/a.txt" | cut -c1-16)" \
    "$(sha256sum < "$work/b.txt" | cut -c1-16)" \
    "$rc"
  if [ "$rc" -ne 0 ]; then
    diff -u "$work/a.txt" "$work/b.txt"
  fi
}

check 5.8 \
  '### 5.8 Parameters and snapshot compatibility (R6, P0-4)' \
  '### 5.9 Interface comparison with `PHASE1_4_S2.md`'

check 12 \
  '## 12. Evaluation set and metrics' \
  '## 13. Staged delivery and review gates'

check 13 \
  '## 13. Staged delivery and review gates' \
  '## 14. Open decisions for Reviewer'

check 11 \
  '## 11. Invariants and validator checks' \
  '## 12. Evaluation set and metrics'

exit 0
```

Invocation, with the archive digest checked first:

```text
sha256sum tmp/PHASE1_4_S2B_DESIGN_r3.md
# 974e49749d1b79f00a9d2f07179caefa2895328b3ceb63283b3e136946fe7811
sh tmp/verify_sections.sh tmp/PHASE1_4_S2B_DESIGN_r3.md \
   icpdf-extractor/docs/PHASE1_4_S2B_DESIGN.md
```

The script ends with `exit 0`, so its status is a liveness signal — every anchor
was unique and every comparison ran — while the per-section `rc=` field carries
the comparison result. Exit 3 remains reserved for a missing or duplicated
anchor; that abort happens before the affected extraction.

### 16.4 Result

```text
974e49749d1b79f00a9d2f07179caefa2895328b3ceb63283b3e136946fe7811 *tmp/PHASE1_4_S2B_DESIGN_r3.md
5.8 lines 148/148 bytes 7934/7934 sha ef1a652297ae1a55/ef1a652297ae1a55 rc=0
12 lines 229/229 bytes 11153/11153 sha dc8c36250a540881/dc8c36250a540881 rc=0
13 lines 25/25 bytes 1770/1770 sha c469afcedd97e2ba/c469afcedd97e2ba rc=0
11 lines 73/80 bytes 4662/5172 sha 204c19409dceea40/2cfe42e8eae5e722 rc=1
@@ -31,11 +31,18 @@
    §5.4; the tuple is empty iff `visual_columns is None`.
 8. Every kept boundary's evidence resolves per §5.3/§9.2; a missing reference
    is an error, not a warning. The evidence kind must match the declared
-   source. `header_canopy` is directed: both anchors resolve, left/right lists
-   are on the correct side, labels equal the anchor text, and the
-   `boundary_edge` position rule holds. `subrule_promoted` has unique in-band
-   assignments and a recomputable ratio. `table_bbox` and `region_extent` match
-   the fresh parse; self-consistency alone is not accepted.
+   source. `header_canopy` is directed: both anchors resolve, each anchor is the
+   head of its nearest-first ref list, left/right lists are on the correct
+   side, labels equal the anchor text, and the `boundary_edge` position rule
+   holds. `subrule_promoted` has one unique source cell per band or is
+   `unresolved`, unique in-band assignments, and a recomputable ratio.
+   `table_bbox` matches the fresh `DetectedTable` exactly. `region_extent`
+   resolves its region by `region_components` equality before matching the
+   record; equal extents alone are never accepted. `structural` refs are unique
+   per `(grid_row, cell_index, edge)`, refs for one `(grid_row, edge)` form a
+   single group that keeps every ref and satisfies
+   `max(edge_xs) - min(edge_xs) <= visual_boundary_tol_pt` with no chain
+   membership, and band counting uses distinct `grid_row` values.
 9. Candidate decisions obey fixed-anchor grouping: `anchor_x` is a member of
    `source_xs`; every `abs(x - anchor_x) <= visual_boundary_tol_pt`; group
    ranges do not overlap (`max(source_xs) < next_anchor_x`); no source x is
```

`rc=0` means the two excerpts are byte-identical. Every per-section count and
digest in this run equals the corresponding value in the r7 run, so tightening
the anchor test from prefix to exact equality changed no excerpt.

The only non-zero comparison is §11, whose unified diff has exactly one hunk,
`@@ -31,11 +31,18 @@`, reproduced above. That hunk begins inside invariant 8 and
ends before invariant 9, so invariants 1–7 and 9–17 are identical by the
construction of the diff, not by inspection. The two `---`/`+++` header lines
that `diff -u` prints are omitted here because they name a fresh temporary
directory on every run; nothing else is omitted.

The script's own exit status is 0: every anchor was unique, in the required
order, and every comparison ran. A heading that is missing or duplicated aborts
the run with status 3, and an end heading that does not follow its start aborts
it with status 4, both before the affected extraction. The four result lines and
the clean exit together attest that every anchor used above was unique and
correctly ordered in both inputs. Both abort paths were exercised: deleting one
anchor from a copy of the r3 archive produced `heading not unique (0
occurrences)` and exit 3, and moving `## 11.` to the end of a copy of this
document produced `heading order invalid` and exit 4.

| Section | What the identity establishes |
| --- | --- |
| §5.8 (N8) | unchanged since r3 in the r9 run above; r10 extends it, see the scope table below |
| §12 (N7) | unchanged since r3 in the r9 run above; r10 adds part D to §12.1 |
| §13 (N8 gates) | unchanged since r3, and still `rc=0` on the r10 text |
| §11 | only invariant 8 differed in the r9 run; r10 also updates invariant 17 |

**Scope after r10.** The result block above is the r9 measurement and is kept as
taken; it does not describe the current file. The same script on the r10
working tree reports:

| Section | r10 lines | r10 bytes | r10 sha, first 16 | rc |
| --- | --- | --- | --- | --- |
| §5.8 | 264 | 14452 | `a7cd3b403bb5d265` | 1 |
| §12 | 286 | 14958 | `b07feadf669b5149` | 1 |
| §13 | 25 | 1770 | `c469afcedd97e2ba` | 0 |
| §11 | 82 | 5306 | `03fcc1db65221af7` | 1 |

§5.8 and §12 differ because r10 edits exactly those two sections, and only
within the four review items: the §5.8 field table, type rules, two-branch
dispatch and raw-bytes loader, and §12.1 part D. §13 is still byte-identical.
§11 gains a second hunk, in invariant 17, which now names
`load_table_params_snapshot` and the per-field validation; invariants 1–16 are
unchanged from the r9 run and invariant 8 is unchanged between r9 and r10. The
r9-to-r10 delta artifact reported in the delivery message shows the changed
hunks; it does not replace this table.

**Scope after r11.** The r10 table above is kept as taken. The r11 working tree
changes §1, §5.8, §11, §12.1, §14, §15 and this subsection, and no other
section. The same script reports:

| Section | r11 lines | r11 bytes | r11 sha, first 16 | rc |
| --- | --- | --- | --- | --- |
| §5.8 | 312 | 17384 | `23a122353ed0ca7b` | 1 |
| §12 | 311 | 17418 | `7b52ea6732b3372f` | 1 |
| §13 | 25 | 1770 | `c469afcedd97e2ba` | 0 |
| §11 | 85 | 5556 | `7a516b2cc29694c2` | 1 |

§13 remains byte-identical across r3, r9, r10 and r11. §5.8 and §12 grow only
inside the r11 items, and §11 changes only invariant 17. The r10-to-r11 delta
artifact reported in the delivery message shows the changed hunks; it does not
replace this table.

**Scope after r12.** The r11 table above is kept as taken. r12 changes §1,
§5.8, §11, §12.1, §14, §15 and this subsection. The same script reports:

| Section | r12 lines | r12 bytes | r12 sha, first 16 | rc |
| --- | --- | --- | --- | --- |
| §5.8 | 331 | 18548 | `a995dc7594c2af7c` | 1 |
| §12 | 323 | 18768 | `6016d0b2150a01df` | 1 |
| §13 | 25 | 1770 | `c469afcedd97e2ba` | 0 |
| §11 | 87 | 5655 | `f6a2f674f5f33a4f` | 1 |

§13 is still byte-identical. §5.8 changes only the root and `params` structure
checks, the loader exception note and one test; §12 changes only the s2b
cross-set row and rules 1, 5 and 6; §11 changes only invariant 17. The
r11-to-r12 delta artifact reported in the delivery message shows the changed
hunks; it does not replace this table.

### 16.5 §11 item by item

| # | Subject | Result |
| --- | --- | --- |
| 1 | null columns iff unresolved | identical |
| 2 | boundary tuple shape, order, containment | identical |
| 3 | `logical_columns` count | identical |
| 4 | `column_projection` authoritative | identical |
| 5 | physical column overlap and canonical bands | identical |
| 6 | overlap recomputation within `1e-6` | identical |
| 7 | visual column invariants | identical |
| 8 | evidence resolution per §5.3/§9.2 | extended by r4/r5, see below |
| 9 | fixed-anchor grouping | identical |
| 10 | cell and assignment word partition | identical |
| 11 | cell bbox, text and reading order | identical |
| 12 | row/column coordinates and id reproduction | identical |
| 13 | header reference and role matrix | identical |
| 14 | physical and S2a fields unchanged | identical |
| 15 | candidate ids and counts unchanged | identical |
| 16 | old artifacts load as unresolved | identical |
| 17 | v1/v2 snapshot replay and validation | identical in the r9 run; extended by r10, r11 and r12 in the working tree |

The invariant-8 extension is exactly five additions from r4 and r5: (a) the
header anchor is the head of its nearest-first ref list; (b) `subrule_promoted`
has one unique source cell per band or is `unresolved`; (c) `table_bbox` equals
the fresh `DetectedTable` exactly; (d) `region_extent` resolves its region by
`region_components` equality before matching the record; (e) `structural` refs
are unique per `(grid_row, cell_index, edge)`, refs for one `(grid_row, edge)`
form one group whose span `max(edge_xs) - min(edge_xs)` is within
`visual_boundary_tol_pt` with no chain membership, and bands are counted by
distinct `grid_row`. These are the closed answers to N2, N3, S3 and S3-span. No
other invariant text changed between r3 and r9.

Content check against the list the r5 review required:

| Required by the r5 review | Where | Present |
| --- | --- | --- |
| Gold annotation and ambiguity as two axes | §12.2 | yes |
| Cross-product table and metric denominators | §12.2, §12.3 | yes |
| Strict v1/v2 schema | §5.8 | yes |
| Duplicate JSON key rejection at load | §5.8 raw-bytes validator, read-path item 2 | yes (r12) |
| S2b-Schema edit allowlist | §5.8 table | yes |
| S1/S2a read-only compatibility boundary | §5.8 rules 7–8 and table | yes |

This is a working-tree comparison, not a substitute for the Reviewer's own
full-document read; it removes the "no hunk in the diff" inference from the
argument.

### 16.6 Delivery channel for the audited bytes

Two rounds of text rendering damaged this evidence. In r7 the `*` of `line_tol`,
the `<=` of the line test and part of the `printf`/`wc`/`diff` calls did not
arrive. In r8 the `<` of `row_end < header_rows` was dropped, so a correct rule
read as `row_end = header_rows`, and the §16.3 fence merged into its heading.
Those are transport defects, not design changes, but they made the evidence
unverifiable, which is the same thing for a review.

A document cannot contain its own bytes: a copy of §16 inside §16 would change
§16. §5.6 is not self-referential, but embedding it would only move the same
transport risk inside this section. Both sections are therefore delivered
out-of-band, with the SHA-256 of each decoded file reported there:

| Section | Extent | Delivery |
| --- | --- | --- |
| §5.6 | the heading `### 5.6` through the line before `### 5.7` | base64 in the delivery message |
| §16 | the heading `## 16.` through the last line of §16.6 | base64 in the delivery message |

Decoding is the check:

```text
base64 -d section_5_6.b64 > section_5_6.md
base64 -d section_16.b64  > section_16.md
sha256sum section_5_6.md section_16.md
```

The delivery message carries each section as base64 with line breaks; if a
renderer re-wraps or joins the lines, stripping spaces and line breaks before
decoding restores the stream. On a system without `base64 -d`, `-D` is the
equivalent.

The decoded files are the authority. The readable text in this document is the
same text, and where a renderer drops a character the decoded file is correct
and the display is not.

**r9 delivery defect (R10-N8FIELDS).** §5.8 was carried as base64 for the first
time in the r9 message. The Reviewer decoded it and read
`merge_column_tol_ptl`. The string is not in the file:
`icpdf.parser.config::TableParams.merge_column_tol_pt` is declared, and the
§5.8 20-name block carries that name and no
other spelling of it. The extra character entered when the base64 was retyped
into the message rather than copied from the file. The same failure class as
the r7 and r8 drops applies in the other direction: a hand-carried channel can
corrupt bytes even when the file is correct. For r10 the four changed items are
therefore delivered as readable text, and §5.8 states each of the 20 names next
to its `config.py` declaration so a name can be checked against the source and
not against a transcript.

§5.6 additionally no longer depends on a bare `<` in its normative sentence:
the `kind` rule is stated with `≤` and `≥` plus a six-row decision table, so the
character that caused the r8 misreading is gone from the rule itself.

**r11 delivery scope.** The base64 table above records the r9 delivery of §5.6
and §16. r11 edits §16.4 and §16.5 only, apart from this paragraph. Those
edited blocks, the five §5.8/§11/§12/§14 changes and the §15 checklist are
delivered as readable text in the r11 message; the r9 base64 remains the record
of the r9 text, not of the current file.
