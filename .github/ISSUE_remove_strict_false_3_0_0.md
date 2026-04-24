# Remove `strict=False` from `compute_total` in 3.0.0

## Background

`inventory.pricing.compute_total` accepts a `strict: bool = True` keyword-only
parameter. When `strict=False`, unknown SKUs in `order.items` are silently
skipped instead of raising `KeyError`, and a `DeprecationWarning` is emitted.

This flag exists **solely as a migration aid** for callers that relied on the
pre-2.x lenient behavior. The lenient path hides catalog-sync errors and
produces silently under-priced totals — exactly the kind of correctness bug
the strict default was introduced to prevent. It is scheduled for removal in
the next major release (**3.0.0**).

The deprecation warning was introduced in 2.x (see `inventory/pricing.py` and
`tests/test_pricing.py::test_strict_false_emits_deprecation_warning`).

## Plan for 3.0.0

Complete removal, not a soft deprecation tightening. Callers who haven't
migrated by 3.0.0 will get a `TypeError: unexpected keyword argument 'strict'`,
which is the correct loud failure for a breaking change.

## Checklist

- [ ] **Code: drop the parameter.** In `inventory/pricing.py::compute_total`:
  - Remove the `strict: bool = True` kw-only parameter (and the `*,` marker
    if no other kw-only params are added).
  - Remove the `if not strict: warnings.warn(...)` block.
  - Remove the `if strict:` branch inside the SKU loop — the unknown-SKU path
    unconditionally raises `KeyError(sku)`.
  - Remove the `import warnings` line if no other code in the module still
    uses it (grep first).
- [ ] **Docstring.** Remove the `strict:` arg entry, the `Warns:` section,
  and the "pre-filter" migration snippet from the `compute_total` docstring.
  Keep the `KeyError` entry under `Raises:` but drop the `strict=True and`
  qualifier.
- [ ] **Tests.** In `tests/test_pricing.py`:
  - Delete `test_strict_false_emits_deprecation_warning` (and any other
    `strict=False` / `DeprecationWarning` tests — grep `strict` and
    `DeprecationWarning` under `tests/`).
  - Keep/strengthen the strict-default test that asserts `KeyError` on
    unknown SKUs; that becomes the only unknown-SKU behavior.
  - Run `pytest -W error::DeprecationWarning` to confirm nothing in the
    suite still trips the old warning path.
- [ ] **README.** Remove any mention of `strict=False` or the migration
    snippet from README.md (grep `strict`). If README has a "Migration from
    1.x" or "Deprecations" section that only covered this flag, delete it.
- [ ] **CHANGELOG.** Under the `3.0.0` section, add a **Breaking changes**
    entry:
    > - `pricing.compute_total` no longer accepts `strict=`. Unknown SKUs
    >   always raise `KeyError`. Callers that need lenient behavior must
    >   pre-filter `order.items` against `catalog` before calling. The
    >   `strict=False` path has been emitting a `DeprecationWarning` since
    >   2.x.
- [ ] **Version bump.** `pyproject.toml` → `version = "3.0.0"`. Confirm
    `python_requires` / classifiers are still accurate while you're in there.
- [ ] **TODO cleanup.** Remove the `TODO(#<this-issue>)` comment in
    `inventory/pricing.py::compute_total` that points to this issue.
- [ ] **Release notes / announcement.** Mention in the 3.0.0 GitHub Release
    body that `strict=` is gone and link to this issue for the rationale.

## Non-goals

- No change to `apply_discount`, `bulk_price`, or the `Order` / `Product`
  models.
- No re-introduction of a "warn and skip" mode under a different name. If
  lenient pricing is genuinely needed, callers should pre-filter explicitly;
  keeping it out of the library surface is the whole point.

## Verification before closing

```
pytest -W error::DeprecationWarning
grep -rn "strict" inventory/ tests/ README.md CHANGELOG.md
```

The grep should return no matches related to `compute_total` (a bare match
of the word "strict" in unrelated prose is fine).
