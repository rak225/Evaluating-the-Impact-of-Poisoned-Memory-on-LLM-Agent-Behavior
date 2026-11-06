# Experimental Protocol (Midpoint)

Team: Srinidhi Ganeshan, Ruchi Kapse, Siddhartha Tamma

## Research question

This project extends Agent Security Bench (ASB) to study how two variables affect an LLM agent exposed to persistent memory:

1. the fraction of poisoned memories in the database, and
2. the retrieval depth `k`, or the number of memories returned for a task.

The midpoint goal is to demonstrate a runnable experimental harness, controlled memory construction, configurable top-k retrieval, evaluation code, and checkable traces. Full-grid results are reserved for the next project stage.

## Current setup

- Baseline: ASB memory-poisoning workflow
- Injection mode: `memory_attack`
- Attack type: `combined_attack`
- Current development model: `ollama/llama3.2:3b`
- Retrieval backend: Chroma
- Embeddings: OpenAI embeddings through `OPENAI_API_KEY`
- Fixed random seed for controlled memory construction: `42`

The original proposal specified Llama-3.1-8B-Instruct. Llama 3.2 3B is used for midpoint development because it can run locally with Ollama. Midpoint observations are therefore treated as feasibility and pipeline-validation results rather than final model-comparison results.

## Experimental variables

| Variable | Current values | Primary owner |
|---|---|---|
| Poisoned-memory fraction `p` | 0, 10, 25, 50, 75, 100% | Srinidhi |
| Retrieval depth `k` | 1, 3, 5, 10 | Ruchi |
| Evaluation and p × k aggregation | full grid once validated runs are available | Siddhartha |

## Controlled memory construction

The controlled poison-rate builder is:

```text
scripts/build_controlled_poison_sweep.py
```

The source database is:

```text
memory_db/direct_prompt_injection/combined_attack_gpt-4o-mini
```

The source contains attack-bearing stored memories. Each usable source record is converted into a paired representation:

- **poisoned counterpart:** the original attack-bearing memory;
- **synthetic clean counterpart:** the same agent/task context with the injected instruction and attacker tool removed, and a benign workflow using a normal tool.

Labels are assigned explicitly at construction time rather than inferred by attacker-tool-name matching. This replaced an earlier heuristic prototype that was found to be unreliable.

A fixed set of 100 underlying memory pairs is sampled with seed 42. Every condition contains exactly 100 records. The same underlying pair population is used across all conditions, with the selected representation changed according to the desired poisoning rate:

| Condition | Clean | Poisoned |
|---:|---:|---:|
| 0% | 100 | 0 |
| 10% | 90 | 10 |
| 25% | 75 | 25 |
| 50% | 50 | 50 |
| 75% | 25 | 75 |
| 100% | 0 | 100 |

The manifest is stored at:

```text
memory_db/controlled_poison_rate_sweep/manifest.json
```

The generated Chroma databases under `memory_db/controlled_poison_rate_sweep/rate_*` are reproducible artifacts and do not need to be versioned.

## Retrieval-depth implementation

Configurable top-k retrieval is implemented in:

```text
retrieval_experiments/retrieval_depth.py
```

and integrated into the ASB agent execution path. The command-line interface exposes:

```text
--retrieval_k
```

The midpoint retrieval sweep uses:

```text
k = 1, 3, 5, 10
```

For `k=1`, the original single-memory prompt format is preserved. For `k>1`, retrieved workflows are combined into the agent context. Retrieval logs record rank, similarity score, memory identifier when available, and poison exposure when explicit labels are present.

## Evaluation

`eval_metrics.py` aggregates ASB result CSV files and computes:

- **ASR:** attack success rate;
- **PNA:** clean-control original-task success rate;
- **NRP:** `PNA × (1 - ASR)`;
- original-task success rate;
- refusal rate;
- memory-found rate.

For automatic extraction of poison rate and retrieval depth, full-grid result filenames should contain:

```text
p<poison_percent>_k<retrieval_k>
```

For example:

```text
combined_attack-test-p25_k3.csv
```

## Midpoint sanity checks

### Retrieval-depth sanity check

The repository contains retrieval-depth traces for `k = 1, 3, 5, 10`. The configured retrieval count matches the number of returned records in these runs.

A useful primary checkable trace is:

```text
experiment_k5.log
```

with `experiment_k1.log` available as a fallback trace.

### Controlled poison-rate endpoint checks

The corrected controlled-memory builder was validated at the two endpoints using `k=1`:

```text
logs/controlled_poison_rate/rate_0.csv
logs/controlled_poison_rate/rate_100.csv
```

The 0% condition retrieved a synthetic clean counterpart and did not find attacker-tool history. The 100% condition retrieved an explicitly poisoned memory. These are pipeline-validation checks, not final poisoning-rate estimates.

## Known limitations and next steps

1. The current clean controls are paired synthetic controls derived from attack-bearing records rather than untouched native ASB clean memories.
2. ASB's `Memory Found` metric is task-specific: a poisoned memory may contain a malicious tool different from the attacker tool being scored for the current run. The final experiment should constrain or stratify poisoned records by task/attacker-tool compatibility, or report general poison exposure separately from task-specific memory-found success.
3. Midpoint experiments use Llama 3.2 3B rather than the originally proposed Llama-3.1-8B-Instruct.
4. The full `p × k` grid has not yet been run with validated matched poisoning conditions.
5. Full-grid result filenames should follow the shared `p<rate>_k<k>` convention so `eval_metrics.py` can aggregate them automatically.

## Ownership

- **Srinidhi Ganeshan:** controlled poisoned-memory construction, poison-rate conditions, endpoint sanity checks, and poisoning methodology.
- **Ruchi Kapse:** configurable top-k retrieval, retrieval logging, retrieval-depth experiments, and integration into agent execution.
- **Siddhartha Tamma:** evaluation metrics, sanity-check evaluation logic, and final poison-rate × retrieval-depth aggregation.
