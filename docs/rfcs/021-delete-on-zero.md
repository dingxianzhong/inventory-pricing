# RFC 021 — `Warehouse.remove` deletion-on-zero

- **Status:** Proposed — under discussion in [#21][issue].
- **Tracking issue:** [#21][issue]
- **Related PRs:** [#26][pr26] (spike, ready for review, `0.2.0`
  milestone), [#14][pr14-style] (pinned the current zero-preservation
  behavior), [#18][pr18-style] (exposed the asymmetry via a
  Hypothesis property).
- **Last updated:** 2026-04-24

[issue]: https://github.com/dingxianzhong/inventory-pricing/issues/21
[pr26]: https://github.com/dingxianzhong/inventory-pricing/pull/26
[pr14-style]: https://github.com/dingxianzhong/inventory-pricing/issues/14
[pr18-style]: https://github.com/dingxianzhong/inventory-pricing/issues/18

## Context

### Baseline (current `main`)

`inventory.models.Warehouse.remove(sku, qty)` currently leaves a SKU
in `stock` when its count is decremented to exactly `0`:

```python
>>> from inventory.models import Warehouse
>>> w = Warehouse(name="w", stock={"A": 3})
>>> w.remove("A", 3)
True
>>> w.stock
{'A': 0}                    # "A" remains, with value 0
```

`add(sku, qty)` does **not** special-case `qty == 0`: it unconditionally
writes `stock[sku] = stock.get(sku, 0) + qty`, which creates a
`{sku: 0}` entry for a previously-absent SKU:

```python
>>> w = Warehouse(name="w")
>>> w.add("A", 0)
>>> w.stock
{'A': 0}                    # "A" created with value 0
```

So on current `main`, both operations can produce or retain
zero-valued entries. This matters because two downstream functions
treat "present at 0" as a meaningful state distinct from "absent":

- `monthly_report([w])` includes a SKU with value `0` in its
  aggregate dict.
- `stock_alert(w, threshold=0)` flags a SKU present with value `0` as
  a zero-stock alert.

Both behaviors are deliberately pinned by regression tests:
zero-preservation in [#14][pr14-style]'s tests added to
`tests/test_reports.py`, and a "present at 0 remains observable after
`add`/`remove` round-trips" property implicit in the weaker
`test_add_then_remove_preserves_effective_stock` from
[#18][pr18-style].

### The asymmetry under debate

`add` and `remove` are consistent with each other — both can leave
zero entries behind. The open question is narrower: **should `remove`
clean up entries whose count has reached `0`, even though `add`
doesn't?**

The user-visible surface that would change is not inside `Warehouse`;
it's that `monthly_report` and `stock_alert(threshold=0)` would stop
seeing those SKUs.

## Proposal

Add an opt-in constructor flag to `Warehouse`:

```python
@dataclass
class Warehouse:
    name: str
    stock: dict[str, int] = field(default_factory=dict)
    delete_on_zero: bool = False
```

When `delete_on_zero=True`, `remove(sku, qty)` does
`del self.stock[sku]` as soon as the count reaches exactly `0`. The
default (`False`) preserves existing behavior exactly.

`add` is **not** changed. `add(sku, 0)` continues to create
`{sku: 0}` regardless of the flag — creating a catalog entry at zero
stock is an explicit caller intent, not an accidental by-product.

A spike implementation of this is up for review in [PR #26][pr26].

## Consequences

### Pros

1. **Cleaner dict invariant.** With the flag enabled, `stock` always
   contains only positive counts. Long-running warehouses no longer
   accumulate zero-valued entries from SKU churn.
2. **Stronger round-trip property.** The weaker
   `test_add_then_remove_preserves_effective_stock` property from
   [#18][pr18-style] could be strengthened to strict dict identity
   for *any* SKU (existing or new), because
   `add(new_sku, n) + remove(new_sku, n)` would be a true no-op on
   `stock`.
3. **Matches common intuition.** Most developers would not expect a
   removed-to-zero SKU to linger.

### Cons

1. **Behavior change for `monthly_report` and `stock_alert`.**
   Pinning "present at 0" as distinct from "absent" was the explicit
   work of [#14][pr14-style] and shows up through both functions:

   | Scenario | Status quo | Option A (flag on) |
   |---|---|---|
   | `add("A", 3); remove("A", 3)`; then `monthly_report([w])` | `{"A": 0}` | `{}` |
   | `add("A", 3); remove("A", 3)`; then `stock_alert(w, threshold=0)` | `["A"]` | `[]` |
   | `add("A", 0)`; then `monthly_report([w])` | `{"A": 0}` | `{"A": 0}` *(unchanged — `add` isn't changing)* |
   | `add("A", 3)`; then `stock_alert(w, threshold=5)` | `["A"]` | `["A"]` *(unchanged — not a zero case)* |

   `stock_alert(threshold=0)` is plausibly a "what did we just run
   out of?" query. Under the flag, that query returns empty — the
   information is erased by bookkeeping.

2. **Loses a real inventory state.** `{"A": 0}` means "we stock A;
   current count is 0." Collapsing it to `{}` conflates "we're out
   of A" with "we don't stock A at all."

3. **Breaks [#14][pr14-style]'s regression tests** when the flag is
   enabled. Under the default they still pass. See [Test impact](#test-impact)
   below for specifics.

4. **Minor compat risk for downstream code** that iterates
   `w.stock` directly for persistence, diffs, or debugging. Our
   public API doesn't promise much about `stock.keys()`, but in
   practice people do rely on it.

## Effects on `monthly_report` and `stock_alert`

See the side-by-side table above. The one-sentence summary: under
the flag, zero-stock SKUs become invisible to both functions **when
they were arrived at via `remove`**. Zero-stock SKUs created
explicitly via `add(sku, 0)` remain visible (because `add` is
unchanged).

If the flag's behavior is eventually promoted to the default and
this distinction is unwelcome, `stock_alert` could grow an explicit
way to request "stocked but at zero" separately from the normal
low-stock query. That's a follow-up design, not part of this RFC.

## Test impact

Under the flag, several tests would **correctly** fail or need
updating. Cataloguing here so reviewers know what's at stake:

**`tests/test_reports.py`** (added in [#14][pr14-style]):

- `test_monthly_report_single_warehouse_preserves_zero_sku` — needs
  deletion or narrowing. Under the flag, a SKU whose zero was
  arrived at via `remove` is no longer preserved. Preservation of
  zeros created via `add(sku, 0)` remains; the test could be
  re-scoped to that narrower case.
- `test_monthly_report_split_preserves_zero_sku_from_one_side`,
  `test_monthly_report_multiple_zero_contributions_sum_to_zero`,
  `test_monthly_report_mixed_zero_and_positive_for_same_sku` —
  all construct their zero-valued entries via direct dict init, so
  they continue to pass. Their docstrings, however, frame the
  behavior as a general rule ("`monthly_report` retains zero"); under
  the flag the rule is narrower. Docstrings and possibly test names
  would want to be adjusted.

**`tests/test_reports_properties.py`** (added in #16):

- The `_pointwise_sum` helper, hand-rolled to preserve zeros rather
  than using `collections.Counter`, remains correct. The
  distributivity and order-independence properties themselves hold
  in both regimes.

**`tests/test_models_properties.py`** (added in [#18][pr18-style]):

- `test_add_then_remove_is_identity_for_existing_sku` — passes
  unchanged.
- `test_add_then_remove_preserves_effective_stock` — passes
  unchanged (asserts via `available()`, not dict equality). Could
  be strengthened to strict dict identity when the flag is enabled.

**`tests/test_warehouse_delete_on_zero.py`** (added in [#26][pr26]):

- New tests already in place that exercise the flag-on path and
  pin the default-off regression. Covers the scenarios this RFC
  discusses.

**New tests that would be added if the flag became the default:**

- A test pinning that `remove(sku, qty)` on a freshly-created SKU
  leaves `"sku" not in w.stock`.
- A test pinning the new `monthly_report` / `stock_alert` semantics
  (companions to the "under the flag" tests already in the spike).

Rough scope: 1–2 tests deleted, 2–3 test names/docstrings revised,
2 new tests added.

## CI impact

None directly. CI runs ruff, flake8, mypy, and pytest; none of these
care about the choice made here. The spike in [#26][pr26] is green on
the full matrix (12 pytest cells × 3 OSes, plus lint and mypy).

## Deprecation timeline — options

No recommendation is made here; all three options are on the table.
The choice depends on how aggressive the project is about
version-bumping and how many (if any) external callers exist.

### Option T1 — conservative (three-step dance)

| Version | Action |
|---|---|
| **0.2.0** | Introduce `delete_on_zero=False`. Emit `DeprecationWarning` **only when the flag is omitted**, pointing at this RFC and asking callers to choose. Default behavior unchanged. |
| **0.3.0** | Flip the default to `True`. Switch the warning: now emitted when `delete_on_zero=False` is passed explicitly. Docs and CHANGELOG call out the new default loudly. |
| **1.0.0** | Remove the flag. `remove` always deletes on zero. Drop the warning, associated tests, and migration scaffolding. |

Two minor releases of warning before the default flips; a third
before the flag disappears. Mirrors the existing
`compute_total(strict=False)` deprecation from #1, which is nice for
consistency.

### Option T2 — compressed (flip and remove at the next major)

| Version | Action |
|---|---|
| **0.2.0** | Introduce `delete_on_zero=False`. No warnings. Opt-in only. *(This is what [PR #26][pr26] implements.)* |
| **Next major** | Flip the default to `True` and remove the flag in one release. CHANGELOG calls out the behavior change as breaking. |

One "experimental opt-in" window, one clean break. Less ceremony,
but less warning for downstreams.

### Option T3 — skip the flag, clean break at next major

| Version | Action |
|---|---|
| **Next major** | `remove` always deletes on zero. No flag ever shipped. CHANGELOG calls out the behavior change as breaking. |

Zero ceremony. Appropriate if we believe the downstream surface is
effectively empty (which for a toy library is plausible) and the
migration — "delete stale `{sku: 0}` entries from your persisted
state" — is a one-liner.

### Trade-off summary

| | T1 (conservative) | T2 (compressed) | T3 (clean break) |
|---|---|---|---|
| Releases to final state | 3 | 2 | 1 |
| Warnings emitted | yes (both default-omitted and explicit-False) | no | no |
| Flag in public API | temporarily (through 1.0.0) | temporarily (through next major) | never |
| Risk of silent breakage for downstreams | very low | low | medium-to-low |
| Engineering effort | highest (sentinel logic, two warning phases) | medium (current spike + one major-bump commit) | lowest |

## Alternatives considered

### Status quo (do nothing)

Keep the current behavior and document the asymmetry prominently in
`Warehouse`'s docstring (which already happens, post-[#22][pr22-style]).
Close [#21][issue] as "won't do." Cheapest option; loses the cleaner
dict invariant and the stronger round-trip property, but avoids the
fallout on `monthly_report` and `stock_alert`.

[pr22-style]: https://github.com/dingxianzhong/inventory-pricing/pull/22

### Per-call `remove(..., delete_on_zero=True)` keyword

Considered; rejected. Callers rarely want different behavior across
`remove` calls on the same warehouse, so the kwarg would usually be
passed with the same value everywhere. Also means the signatures of
`add` and `remove` drift apart for no benefit.

### Environment variable (`INVENTORY_DELETE_ON_ZERO=1`)

Considered; rejected. Global state, untestable in isolation without
monkey-patching, surprising in library code. Easiest to retract but
worst ergonomics.

### Redesign `monthly_report` / `stock_alert` instead

Rather than changing `Warehouse`, change the reporters to filter
out zero entries themselves. This leaves `Warehouse.stock` as-is
and makes the "out of stock" vs. "not carried" distinction an
explicit parameter on the reporters. Plausible, but it's a larger
surface change affecting two public functions instead of one, and
it doesn't give us the cleaner dict invariant that Option A does.

## Open questions

- Is the `monthly_report` / `stock_alert` fallout acceptable in
  principle? This is the core question.
- If yes: which of T1 / T2 / T3?
- Is the constructor flag worth shipping at all, or should we wait
  for a major bump and do T3?

Discussion is open on [#21][issue].
