# MAC-DAST Interface Layer

The `interface/` directory contains the telemetry harnesses and data consolidation logic that bridges the gap between raw instrumentation and the MAC-DAST autonomous agents.

## Core Components

### 1. Telemetry Aggregator (`aggregator.py`)
Consolidates telemetry from multiple sources into a unified, agent-friendly JSON stream.
- **PHP Data**: Merges coverage (files/lines) and state snapshots (sessions, cookies).
- **C/C++ Data**: Aggregates eBPF trace events, including uprobe hits and extracted function arguments.
- **Trace IDs**: Assigns unique UUIDs to every aggregated event for cross-harness correlation.

### 2. PHP Xdebug Harness (`php_xdebug/`)
Provides deep visibility into PHP application execution.
- `runner.py`: Orchestrates HTTP requests to target applications and retrieves Xdebug coverage files.
- `coverage_parser.py`: Transforms raw Xdebug output into structured logic-path models.
- `state_observer.py`: Detects meaningful transitions in application state (e.g., privilege escalation, session tampering) between requests.
- `routing.py`: Maps URL patterns to specific entry-point scripts to help agents navigate the codebase.

### 3. C++ eBPF Harness (`cpp_ebpf/`)
Coordinates with the `syscall-module` to trace native binary execution.
- `harness.py`: Manages binary execution and dynamically attaches eBPF uprobes to specific symbols.
- **Argument Extraction**: Automatically retrieves string-based function arguments (SQL queries, file paths) from the eBPF kernel stream.

## Telemetry Schema

All telemetry is aggregated into a unified format:

```json
{
  "timestamp": "2026-06-07T02:00:00Z",
  "trace_id": "uuid-v4",
  "source": "php|cpp",
  "coverage": {
    "file.php": [10, 11, 15]
  },
  "state": {
    "session": { "user_id": 42 }
  },
  "events": [
    { "type": "uprobe", "symbol": "mysql_query", "arg": "SELECT * FROM users" }
  ]
}
```
