# Local model qualification — exploratory wave

## Status

This document records an exploratory local-model test wave performed on
2026-09-22. It is evidence about a local runtime, not an executor adoption
decision, a product dependency, or scientific proof of capability.

No Arkx source code, fixtures, contracts, or experiment results were changed
by this wave. The tests were run outside the repository's experiment harness.

## Controlled intent

The same small coding task was used across models:

> Write a Python function that raises `ValueError("value is required")` for
> `None`, returns the input otherwise, and show the correct exception test.

The initial smoke test asked for `OK`. A second functional prompt constrained
the output to the function and `pytest.raises(ValueError,
match="value is required")`. Models were started one at a time through the
direct Ollama executable; the previously loaded model was stopped before
switching when possible.

This was a capability probe only. It did not control temperature, context
window, quantization, thread count, or hardware telemetry sufficiently for a
comparative benchmark. Therefore latency is indicative, not comparable
evidence.

## Environment

| Dimension | Recorded value |
| --- | --- |
| Runtime | Ollama 0.34.3 |
| Runtime executable | `C:\Users\igorb\AppData\Local\Programs\Ollama\ollama.exe` |
| Intended hardware envelope | 16 GB RAM, as reported for this evaluation |
| Test date | 2026-09-22 |
| Repository effect | none; existing local Arkx changes were preserved |

## Results

| Model | Local artifact | Observation | Qualification state |
| --- | --- | --- | --- |
| Gemma 3 4B | `gemma3:4b`, 3.3 GB | Passed `OK`; generated the requested function and a correct `pytest.raises` assertion. Functional run took about 25 s. | Candidate for deeper qualification |
| Granite 3.3 8B | `granite3.3:8b`, 4.9 GB | Passed the `OK` smoke test in about 23 s. Functional correctness was not fully captured in this wave. | Smoke-qualified only |
| Phi-4-mini | `phi4-mini:latest`, 2.5 GB | Executed the task in about 14 s; response capture was not reliable enough for a correctness verdict. | Inconclusive |
| Nemotron Nano 4B | `nemotron-3-nano:4b`, 2.8 GB | Returned `OK`, but exposed a `Thinking` block despite the bounded-output request. | Rejected for clean executor output until controlled |
| Qwen2.5-Coder 3B | `qwen2.5-coder:3b`, 1.9 GB | Responded, but an earlier coding trial produced an invalid exception test using value equality instead of an exception assertion. | Candidate with review gate |
| Qwen2.5-Coder 7B | `qwen2.5-coder:7b`, 4.7 GB | Passed an isolated `OK` smoke test; broader capture was inconsistent during model switching. | Smoke-qualified only |
| Qwen2.5-Coder 14B | `qwen2.5-coder:14b`, 9.0 GB | Process executed, but the final response was not auditable in the captured terminal output. | Inconclusive |
| Qwen3.6 35B | `qwen3.6:35b`, 22 GB | Process was attempted on the 16 GB envelope; no auditable response was captured. | Not qualified for this envelope |
| DeepSeek-R1 7B | `deepseek-r1:7b`, 4.7 GB | Repeated isolated attempts produced no captured response within the test window. | Not qualified |
| GLM4 9B | `glm4:9b`, 5.5 GB | Installed; smoke execution completed through the interactive runtime, but output capture was inconclusive. | Inconclusive |
| StarCoder2 7B | `starcoder2:7b`, 4.0 GB | Installed; smoke execution completed through the interactive runtime, but output capture was inconclusive. | Inconclusive |

## Interpretation

The strongest directly observed result was Gemma 3 4B for bounded coding output.
Granite 3.3 8B and Qwen2.5-Coder 7B remain plausible candidates, but require
the same functional task through a machine-readable adapter before adoption.
Phi-4-mini is attractive for lightweight work because of its size and observed
latency, but it has not yet passed a correctness gate.

Nemotron's exposed reasoning is a concrete executor-interface concern: a model
may be useful internally while still violating the output contract. It must
not be silently repaired or accepted as clean output.

The 35B artifact is larger than the reported 16 GB RAM envelope and produced
no auditable result. It is not evidence that the model is unusable in every
environment; it is simply unqualified here.

These observations support a portfolio hypothesis rather than a single-model
choice:

- a small model can handle bounded auxiliary tasks;
- a code-oriented model may handle implementation tasks;
- a separate review model may be useful for verification;
- routing among them must remain explicit and observable.

No routing, retry, fallback, executor switch, acceptance, promotion, or
automatic selection was introduced by this test wave.

## Limitations and next experiment

The Ollama interactive terminal emitted control sequences and, for some
models, did not provide a reliably machine-readable response to the calling
shell. Consequently, `executed` must not be interpreted as `accepted` or
`passed`.

The next qualification step should use one fixed adapter and JSON response
capture, with:

1. fixed prompt and generation settings;
2. fixed timeout and maximum output size;
3. syntax and test execution of generated Python;
4. explicit output-contract validation;
5. memory and tokens-per-second measurements;
6. repeated trials under the same model/environment identity.

Until that exists, the states above remain exploratory observations, not
promotion evidence.
