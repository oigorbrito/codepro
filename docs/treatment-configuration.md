# Treatment Configuration Manifest v1

A treatment is not identified only by the name of an executor or model. The complete configuration that can affect the observation must be frozen.

## Frozen identity

The manifest records:

- executor identity and version;
- provider and model identity when applicable;
- immutable model revision when available, otherwise explicit disclosure that the provider does not expose one;
- prompt reference and content hash;
- tool-surface reference and content hash;
- provider-routing policy;
- model/executor parameters;
- bounded attempts and timeout;
- fallback policy and targets;
- deterministic seed when supported, or explicit disclosure when unsupported.

A change to any of these fields produces a different configuration hash and therefore a different treatment identity.

## Provider limitations

Provider-hosted models may expose a stable model name without exposing the exact serving-weight revision. CodePro records that limitation rather than treating the name as an immutable model binary.

Likewise, unsupported seeding is not replaced with a fabricated seed. Stochastic stability must then be addressed through the frozen repetition design.

## Boundary

```text
MODEL_NAME != IMMUTABLE_MODEL_REVISION
SAME_EXECUTOR != SAME_TREATMENT_CONFIGURATION
PROMPT_CHANGE != SAME_TREATMENT
SILENT_FALLBACK != VALID_REPLICATION
UNSUPPORTED_SEED != DETERMINISTIC_RUN
```
