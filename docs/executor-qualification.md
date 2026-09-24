# P8.1 executor qualification contracts

P8.1 defines an experimental boundary for describing executors and recording external observations. It does not integrate, execute, select, rank, accept, promote, or invoke an executor.

`ExecutorIdentity` and advertised capabilities are metadata. They are not evidence of reliable capability. `ExecutorObservation` preserves acceptance, patch verification, costs, time, retries, replans, handoffs, regressions, and other measurements exactly as supplied; unknown values remain `None` and explicit zero remains zero.

Comparisons use an explicit axis. `EXECUTOR` requires the same task revision, acceptance definition, model, environment, budget, and P7 treatment while varying executor. `TREATMENT` requires the same task, executor, model, environment, and budget while varying P7 treatment. Divergent controls are `INCOMPARABLE`; missing control evidence is `UNKNOWN`.

`COMPLETED` with `accepted=False` is a valid observed outcome. Infrastructure, executor, budget, and blocked outcomes are not silently converted into rejection. P8 records external acceptance; it never infers acceptance from patch verification or execution completion.

Summaries aggregate dimensions without producing a winner or global ranking. Promotion and removal decisions remain outside P8.

Decision `0035` adds the first executable paired-protocol gate. It requires at
least two executor identities, complete task/replicate cells, shared verifier
and instrumentation identities, and matching control dimensions before a
comparison can be called `QUALIFIABLE`. This is a comparability gate only; it
does not rank or promote an executor. The real protocol remains
`NOT_EXECUTED` until concrete executors produce raw observations.
