# Evaluating the Impact of Poisoned Memory on LLM Agent Behavior

This repository extends **Agent Security Bench (ASB)** to study how persistent-memory poisoning affects LLM-based agents. Our project focuses on two variables: the **fraction of poisoned memories** in an agent's memory database and the **retrieval depth `k`** used when selecting prior workflows.

## Team

- **Srinidhi Ganeshan** — controlled poisoned-memory construction and poison-rate experiments
- **Ruchi Kapse** — configurable top-k retrieval and retrieval-depth experiments
- **Siddhartha Tamma** — evaluation metrics and poison-rate × retrieval-depth analysis

## Midpoint status

The repository currently contains:

- a runnable ASB memory-attack baseline using Ollama;
- a controlled poison-rate database builder with exact 0%, 10%, 25%, 50%, 75%, and 100% conditions;
- configurable retrieval depths `k = 1, 3, 5, 10`;
- retrieval logs and checkable execution traces;
- evaluation code for ASR, PNA, NRP, task success, refusal rate, and memory-found rate;
- endpoint sanity checks for the corrected 0% and 100% controlled-memory conditions.

The current development model is **Llama 3.2 3B** through Ollama. These midpoint runs are intended to validate the experiment pipeline rather than serve as final reported model results.

## Repository structure

```text
config/MP.yml                              memory-attack configuration
scripts/agent_attack.py                   ASB experiment launcher
scripts/build_controlled_poison_sweep.py  controlled poison-rate builder
retrieval_experiments/retrieval_depth.py  configurable top-k retrieval
main_attacker.py                          main attack/evaluation entry point
eval_metrics.py                           metric aggregation
PROTOCOL.md                               current experimental protocol
logs/controlled_poison_rate/              endpoint sanity-check CSVs
logs/retrieval/                           retrieval metadata logs
results/                                  evaluation outputs and sanity checks
```

## Requirements

The midpoint setup was tested on Windows with Python 3.11 and Ollama.

You need:

- Python 3.11
- Ollama
- Miniconda/Conda available on `PATH` because the ASB runtime invokes `conda list`
- an OpenAI API key for the Chroma embedding function

The OpenAI API key is used for embeddings; local LLM inference is performed by Ollama.

## Setup on Windows PowerShell

Clone the repository and enter it:

```powershell
cd C:\path\to\Evaluating-the-Impact-of-Poisoned-Memory-on-LLM-Agent-Behavior
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Install/pull the local model:

```powershell
ollama pull llama3.2:3b
```

For the current PowerShell session, make Conda available and use UTF-8 console output:

```powershell
$env:Path = "$env:USERPROFILE\miniconda3\condabin;$env:USERPROFILE\miniconda3\Scripts;$env:Path"
$env:PYTHONIOENCODING="utf-8"
```

Set the OpenAI API key privately in the environment:

```powershell
$env:OPENAI_API_KEY="YOUR_KEY_HERE"
```

Do not commit API keys or `.env` files.

## Run the baseline memory attack

The default midpoint configuration is in `config/MP.yml` and currently uses:

```text
model: ollama/llama3.2:3b
attack type: combined_attack
memory attack: enabled
retrieval_k: 1
```

Run:

```powershell
python .\scripts\agent_attack.py --cfg_path .\config\MP.yml
```

## Build controlled poison-rate databases

Run:

```powershell
python .\scripts\build_controlled_poison_sweep.py
```

The builder uses seed 42 and creates six fixed-size 100-memory conditions:

```text
0%   -> 100 clean / 0 poisoned
10%  -> 90 clean  / 10 poisoned
25%  -> 75 clean  / 25 poisoned
50%  -> 50 clean  / 50 poisoned
75%  -> 25 clean  / 75 poisoned
100% -> 0 clean   / 100 poisoned
```

The generated databases are written under:

```text
memory_db/controlled_poison_rate_sweep/rate_*
```

The versioned manifest is:

```text
memory_db/controlled_poison_rate_sweep/manifest.json
```

The labels are assigned by construction. They are **not** inferred by searching memory text for attacker-tool names.

## Run a controlled condition directly

Example: 0% poison rate at `k=1`:

```powershell
python .\main_attacker.py `
  --llm_name "ollama/llama3.2:3b" `
  --attack_type combined_attack `
  --use_backend ollama `
  --attacker_tools_path data/attack_tools_test.jsonl `
  --res_file "logs/controlled_poison_rate/rate_0.csv" `
  --database "memory_db/controlled_poison_rate_sweep/rate_0" `
  --retrieval_k 1 `
  --read_db `
  --memory_attack
```

For the 100% endpoint, replace `rate_0` with `rate_100` in both the result-file and database paths.

## Retrieval-depth experiments

The retrieval extension supports:

```text
k = 1, 3, 5, 10
```

The command-line option is:

```text
--retrieval_k <k>
```

`retrieval_experiments/retrieval_depth.py` retrieves the top-k Chroma memories, extracts stored workflows, combines them for `k > 1`, and records rank, similarity score, memory ID when available, and poison exposure when labels are available.

Representative traces are included at the repository root:

```text
experiment_k1.log
experiment_k3.log
experiment_k5.log
experiment_k10.log
```

`experiment_k5.log` is the primary midpoint retrieval trace; `experiment_k1.log` can be used as a fallback trace.

## Evaluation

`eval_metrics.py` reads ASB result CSVs and computes:

- attack success rate (ASR)
- clean-control task success (PNA)
- NRP = `PNA × (1 - ASR)`
- original-task success rate
- refusal rate
- memory-found rate

For full-grid experiments, name result files with both the poison percentage and retrieval depth:

```text
p<poison_percent>_k<k>
```

For example:

```text
combined_attack-test-p25_k3.csv
```

Then aggregate them with:

```powershell
python .\eval_metrics.py "logs/**/*.csv" --out results/summary.csv
```

## Midpoint limitations

The current controlled clean memories are **paired synthetic clean controls** derived from poisoned source records; they are not untouched native ASB clean memories.

Also, ASB's `Memory Found` metric is task-specific. A retrieved memory can be genuinely poisoned while containing a malicious tool different from the attacker tool selected for the current evaluation run. Final experiments will therefore match or stratify poisoned memories by task/attacker-tool compatibility, or report general poisoned-memory exposure separately from ASB's task-specific memory-found metric.

The full poison-rate × retrieval-depth grid has not yet been completed with the final matched poisoning protocol.

See [`PROTOCOL.md`](PROTOCOL.md) for the current experimental design and remaining work.

## Upstream project

This project is derived from **Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents**, ICLR 2025.

Upstream repository: https://github.com/agiresearch/ASB

Paper: https://arxiv.org/abs/2410.02644

The original ASB code and license are retained in this repository. Our project-specific changes focus on controlled poison-rate construction, configurable memory-retrieval depth, and evaluation of their interaction.
