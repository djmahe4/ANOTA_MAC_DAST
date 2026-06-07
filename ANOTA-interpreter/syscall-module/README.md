# syscall-tracepoint (MAC-DAST Extended)

## Prerequisites

1. Install Rust nightly: `rustup toolchain install nightly`
2. Install `bpf-linker` from source (to ensure LLVM 22 compatibility):
   ```bash
   cargo +nightly install --git https://github.com/aya-rs/bpf-linker bpf-linker --branch main --force
   ```
3. Set up the workspace toolchain:
   ```bash
   # In ANOTA-interpreter/syscall-module/
   cat > rust-toolchain.toml <<EOF
   [toolchain]
   channel = "nightly"
   components = ["rust-src"]
   targets = ["x86_64-unknown-linux-gnu"]
   EOF
   ```

## Build eBPF

```bash
cargo run --package xtask -- build-ebpf --release
```

This command uses the `xtask` build runner to compile the eBPF kernel object for the `bpfel` target with full optimizations (LTO, high opt-level), which are required for complex argument extraction logic.

## Build Userspace

```bash
cargo build --package syscall-tracepoint --release
```

## Run

```bash
RUST_LOG=info sudo ./target/release/syscall-tracepoint
```

The userspace daemon exposes a UNIX domain control socket at `/tmp/anota_syscall.sock`. MAC-DAST extends the original protocol with dynamic uprobe support:

```
START                     # Enable tracing for every process
START <pid>               # Enable tracing only for the specified PID
STOP                      # Disable tracing
UPROBE <path> <function>  # Dynamically attach an eBPF uprobe to the specified binary/symbol
```

### Argument Extraction

When a `UPROBE` is triggered, the eBPF handler automatically attempts to extract the first function argument as a string from user-space memory (using `bpf_probe_read_user_str`). The extracted data is emitted via `aya-log` and collected by the user-space tracer.

### Development Shortcut

When running tests or developing on a machine without eBPF permissions, export
`ANOTA_SYSCALL_SKIP_EBPF=1` before launching the daemon. In this mode the Rust
process still brings up the control socket but skips loading/attaching the
kernel programs, which avoids requiring root access. Combine this with the
nightly toolchain commands above (e.g. `ANOTA_SYSCALL_SKIP_EBPF=1 cargo +nightly xtask run`).

## Integration Test

After compiling the daemon, you can run the Python-side integration test (from
the repo root) to ensure end-to-end communication works:

```bash
./python anota_syscall_integration_test.py
```

This script automatically builds the Rust binary if needed, starts it with
`ANOTA_SYSCALL_SKIP_EBPF=1`, and invokes the `ANOTA_SYSCALL_SIGNAL_START/STOP`
helpers. Use it whenever you change the control-socket protocol.

## Collect Tracepoint Events
```
sudo cat /sys/kernel/debug/tracing/available_events |grep syscalls > syscall_event_list.txt
sudo cat /sys/kernel/debug/tracing/events/syscalls/sys_enter_access/format
```
