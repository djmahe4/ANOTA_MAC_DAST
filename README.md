# ANOTA MAC-DAST: Multi-Agent Context-Aware Dynamic Application Security Testing

ANOTA MAC-DAST is a hardened and extended fork of the ANOTA framework, specifically designed for **autonomous logic abuse detection**. It combines high-performance C-level instrumentation with a multi-agent telemetry aggregation layer to build formal Business Logic Models (BLM) and synthesize complex multi-step exploits.

This repository contains the full artifact for the MAC-DAST framework, extending the original ANOTA paper's base with enhanced stability, support for unhashable objects, and a dual PHP/C++ telemetry harness.

---

## Key Enhancements in MAC-DAST

- **Hardened Instrumentation Base**: Refactored `ANOTA_TAINT` and `ANOTA_WATCH` to use high-performance C hashtables (`_Py_hashtable_t`). This provides support for unhashable objects and prevents infinite recursion during security checks.
- **Memory Safety & Stability**: Implemented deallocation-aware policy cleanup using `_Py_Dealloc` hooks to prevent address-reuse vulnerabilities. Added recursion guards and error-state preservation to all C-level hooks.
- **Dynamic eBPF Tracing**: Extended the `syscall-module` with dynamic `UPROBE` support, allowing agents to trace arbitrary C/C++ functions and extract string arguments (e.g., SQL queries, file paths) directly from user-space memory.
- **Dual-Language Telemetry**: Integrated `PHP_XDEBUG` coverage and state observation alongside the native C/C++ trace harness.
- **Unified Telemetry Stream**: A specialized `TelemetryAggregator` consolidates coverage, state transitions, and trace events into a unified JSON stream for BLM extraction agents.
- **Autonomous Attack Generation**: Specialized agents synthesize logic exploits (step-skipping, parameter tampering, race conditions) using `Qwen 2.5 Coder`, grounded in formal Business Logic Models.
- **High-Fidelity Validation**: A 'Critic' agent using `mistral-nemo` reality-checks hypothesized attacks against ground-truth telemetry, applying a hybrid confidence score (LLM judgment + keyword-match metrics).
- **Automated Reproduction**: Confirmed vulnerabilities trigger the automatic generation of standalone Python reproduction scripts for rapid verification and fix-validation.

## Runtime Permissions & Security

MAC-DAST operates across different privilege levels. To ensure smooth execution:

1.  **Trace Daemon (Root)**: The `syscall-tracepoint` process **must** run as root (via `sudo`) to manage eBPF programs and uprobes.
2.  **Control Socket**: The daemon automatically sets the `/tmp/anota_syscall.sock` permissions to `666` (world-writable) to allow the non-root logic engine to send commands.
3.  **Readiness Check**: Use the provided diagnostic tool to verify your environment before a full scan:
    ```bash
    python3 runtime_check.py
    ```

### Recommended Workflow
- Terminal 1 (Root): `cd ANOTA-interpreter/syscall-module && sudo ./target/release/syscall-tracepoint`
- Terminal 2 (User): `python3 logic_engine/orchestrator.py`

---

## Directory Overview

- [`ANOTA-interpreter/`](ANOTA-interpreter/) – Hardened CPython 3.10.13 fork. Includes C-level hashtable refactors and dealloc hooks. See its [README](ANOTA-interpreter/README.md) for build steps.
- [`ANOTA-interpreter/syscall-module/`](ANOTA-interpreter/syscall-module/) – Extended Rust workspace for eBPF tracing. Now supports dynamic uprobes and string argument extraction. Refer to its [README](ANOTA-interpreter/syscall-module/README.md).
- [`logic_engine/`](logic_engine/) – **[NEW]** The "brain" of MAC-DAST. Contains the LangGraph orchestrator, `iii-engine` durable workers, and the multi-tier agent memory pipeline.
- [`interface/`](interface/) – **[NEW]** MAC-DAST interface layer. Contains the Telemetry Aggregator, PHP Xdebug harness, and C++ uprobe coordinator.
- [`agents/prompts/`](agents/prompts/) – **[NEW]** Prompt templates for the agents.
- [`SupplementaryMaterials/`](SupplementaryMaterials/) – Original ANOTA evaluation data and user study details.

---

## How to Navigate the Artifact

1. **Instrumentation Base**: Start with `ANOTA-interpreter/README.md` to build the hardened interpreter and run the security primitives.
2. **eBPF Tracing**: Move to `ANOTA-interpreter/syscall-module/README.md` to set up the uprobe and syscall monitoring daemon.
3. **Logic Engine & Agents**: Explore `logic_engine/` to see how the multi-agent swarm processes telemetry and synthesizes logic attacks using `mistral-nemo` and `Qwen 2.5 Coder`.
4. **Telemetry & Aggregation**: Explore `interface/` to see how coverage and state data are consolidated for the agents.
5. **Original Artifact**: Consult the `SupplementaryMaterials/` for baseline performance data and the annotation studies described in the original paper.
