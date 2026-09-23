# P7 experimental composition harness

P7 defines removable treatment descriptions and records externally supplied observations. It does not execute P1–P6, select an executor, retry, replan, route, accept, promote, or produce `PASS`.

Each treatment contains a canonical immutable tuple of enabled mechanisms. Mechanisms are serialized in the fixed order P1 through P6, regardless of input order. The initial fixture contains only A–F; adaptive composition G is deliberately absent until an adaptive mechanism exists to qualify.

Trials are comparable only when task, executor, model, environment, and budget are all known and equal. Divergence is `INCOMPARABLE`; missing identity evidence is `UNKNOWN`. Treatment composition is recorded separately and is not executed by P7.

Summaries count supplied measurement observations and preserve absence. They never impute zero or false, and they do not represent acceptance or promotion.
