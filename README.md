# Anota: Identifying Business Logic Vulnerabilities via Annotation-Based Sanitization

This repository contains the full artifact for the ANOTA paper. Each subdirectory ships with its own README that documents build steps, test procedures, and evaluation notes. The top-level README stays intentionally high level and simply orients you toward the right component.

---

## Directory Overview

- [`ANOTA-interpreter/`](ANOTA-interpreter/) – ANOTA’s CPython 3.10.13 fork that introduces the `ANOTA_EXECUTION`, `ANOTA_WATCH`, `ANOTA_TAINT`, and `ANOTA_SYSCALL` primitives. See `ANOTA-interpreter/README.md` for detailed build and validation instructions.
- [`ANOTA-interpreter/syscall-module/`](ANOTA-interpreter/syscall-module/) – Rust workspace that provides the eBPF tracepoints used by the syscall policies. Refer to `ANOTA-interpreter/syscall-module/README.md`.
- [`SupplementaryMaterials/annotation_study_details.md`](SupplementaryMaterials/annotation_study_details.md) – Details about the annotation user study participants, feedback, and results.
- [`SupplementaryMaterials/cmp-with-DBI/`](SupplementaryMaterials/cmp-with-DBI/) – DynamoRIO and Valgrind memory-tracing baselines plus the scripts used for the performance comparison in the paper.
- [`SupplementaryMaterials/cmp-with-DBI/perf-data/`](SupplementaryMaterials/cmp-with-DBI/perf-data/) – Supplementary data for performance comparison with DBIs.
- [`SupplementaryMaterials/cwe_top_40.md`](SupplementaryMaterials/cwe_top_40.md) – Analysis of Anota's support for the CWE Top 40 Security Weaknesses.
- [`SupplementaryMaterials/perf-benchmark.md`](SupplementaryMaterials/perf-benchmark.md) – Performance evaluation details and benchmark results.
- [`SupplementaryMaterials/skipped_applications.md`](SupplementaryMaterials/skipped_applications.md) – List of applications skipped in the evaluation and the reasons.
- [`SupplementaryMaterials/user-study/`](SupplementaryMaterials/user-study/) – Annotation training packet and real-world developer survey materials.


---

## How to Navigate the Artifact

1. Start with `ANOTA-interpreter/README.md` to build the instrumented interpreter and run the ANOTA samples.
2. Move to `ANOTA-interpreter/syscall-module/README.md` when you need syscall tracing or you want to use it w/o ANOTA's CPython interpreter.
3. Use the documentation inside `SupplementaryMaterials/cmp-with-DBI/` for the performance comparisons against the DBI memory trace baselines.
4. Consult `SupplementaryMaterials/user-study/` if you are re-running the annotation study or the real-world developer study survey described in the paper.
