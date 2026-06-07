# MAC-DAST Logic Engine

The `logic_engine/` directory contains the cognitive core of the MAC-DAST framework. It implements the multi-agent orchestration, the 4-tier cognitive memory pipeline, and the attack synthesis logic.

## Core Components

### 1. Agent Orchestrator (`orchestrator.py`)
A Supervisor-Worker network built on **LangGraph**. It routes logical tasks between specialized agents:
- **`analyze_trace`**: Consolidates 4-tier memory and prepares analysis context.
- **`generate_attack`**: Synthesizes multi-step logic exploits using the **Attack Generator**.
- **`validate_attack`**: Executes payloads and reality-checks outcomes using the **Validator Agent**.

### 2. Offensive Tooling (`agents/mutator.py`, `agents/concurrent_attacker.py`)
Provides the "hands" for the Attack Generator:
- **`RequestMutator`**: Implements parameter tampering (value replacement/omission) and sequence reordering (step-skipping).
- **`ConcurrentAttacker`**: Async thread spawner designed to trigger and verify race conditions.
- **`AttackExecutor`**: A routing layer that executes synthesized payloads on the physical PHP/C++ harnesses.

### 3. Validation & Reproduction (`agents/validator.py`, `agents/repro_gen.py`)
Eliminates false positives and provides actionable evidence:
- **Validator Agent**: A 'Critic' using `mistral-nemo` to judge ground-truth telemetry. It computes a hybrid confidence score:
    - **60% LLM Subjective Judgment**: Deep semantic analysis of the trace.
    - **40% Objective Keyword Match**: Correlation between hypothesized outcomes and telemetry keywords.
- **Reproduction Generator**: Synthesizes standalone Python/Bash scripts for every confirmed vulnerability, ensuring developers can instantly reproduce findings.

### 4. Durable Execution (`iii-engine`)
...Integrated with the **iii-engine** Python SDK to ensure durable, long-running agent workflows.
- `process_trace`: A durable function triggered whenever new telemetry is aggregated.
- `consolidate`: A background worker that manages memory tier promotion and decay.

### 3. Agent Configuration (`agent_config.py`)
Centralized settings for local LLM models (via Ollama) and logical parameters:
- **Reasoning**: `mistral-nemo` (1M context) for orchestration.
- **Coding/Extraction**: `qwen2.5-coder` for code analysis.
- **Embeddings**: `bge-m3` for semantic search.
- **Logic**: Configuration for RRF search `k` and confidence decay rates.

## Multi-Tier Memory Pipeline

MAC-DAST implements a 4-tier memory architecture to prevent context exhaustion and hallucination:

1.  **Working Memory**: The current active context window in LangGraph.
2.  **Episodic Memory**: Raw execution traces and state transitions (stored in `data/blm.db`).
3.  **Semantic Memory**: Hardened business logic rules and the repository's structural knowledge graph (built via `codebase-memory-mcp`).
4.  **Procedural Memory**: Reusable attack strategies and security policies.

### Hybrid Search (RRF)
Agents retrieve context using a three-stream search combined via **Reciprocal Rank Fusion (RRF)**:
- **BM25**: Keyword matching over execution logs (SQLite FTS5).
- **Vector**: Semantic similarity using BGE-M3 embeddings.
- **Graph**: Structural relationships from the codebase.

## Setup & Running

### 1. Initialize Virtual Environment
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt # (Coming soon)
```

### 2. Start the Orchestrator Worker
```bash
python3 logic_engine/orchestrator.py
```
This worker will connect to the `iii-engine` and wait for telemetry events.
