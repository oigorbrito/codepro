# Decision 0154 — Test discovery boundary

Date: 2026-09-25

## Result

The current pytest configuration collects only the product test tree. A clean
collection produced exactly 400 test items, all under `tests/`; no historical
`logs/` file, copied workspace, nested repository, or experiment JSON was
collected as a test.

The complete provider-free suite then passed 400/400 on Python 3.13 in 3.00s,
with 3 warnings and no failures. The run used `-p no:cacheprovider` to avoid
creating host cache artifacts. This is local suite evidence only; it is not
provider, benchmark, or executor qualification evidence.

## Decision

The discovery boundary is accepted for the current checkout. Historical log
retention remains a separate concern; no logs or workspaces were deleted.
