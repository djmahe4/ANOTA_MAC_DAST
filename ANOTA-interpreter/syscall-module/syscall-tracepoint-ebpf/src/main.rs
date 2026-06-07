#![no_std]
#![no_main]
mod process;
mod file;

use aya_ebpf::{
    macros::{tracepoint, uprobe},
    programs::{TracePointContext, ProbeContext},
    helpers::bpf_probe_read_user_str_bytes,
    EbpfContext,
};
use aya_log_ebpf::info;
use syscall_tracepoint_common::BUF;

#[uprobe]
pub fn generic_uprobe(ctx: ProbeContext) -> u32 {
    let pid = ctx.pid();
    
    // Attempt to extract the first argument as a string
    // In x86_64, the first arg is in %rdi, which ctx.arg(0) should map to.
    let arg0: *const u8 = match ctx.arg(0) {
        Some(ptr) => ptr,
        None => {
            info!(&ctx, "uprobe hit by PID {} (no arg0 found)", pid);
            return 0;
        }
    };

    // Get a per-CPU buffer to avoid stack overflow
    let buf = unsafe {
        match BUF.get_ptr_mut(0) {
            Some(ptr) => &mut *ptr,
            None => return 0,
        }
    };

    // Safely read string from user space
    let res = unsafe {
        bpf_probe_read_user_str_bytes(arg0, &mut buf.buf)
    };

    match res {
        Ok(bytes) => {
            let s = unsafe { core::str::from_utf8_unchecked(bytes) };
            info!(&ctx, "uprobe PID {} arg: {}", pid, s);
        }
        Err(_) => {
            info!(&ctx, "uprobe PID {} (read error)", pid);
        }
    }

    0
}

#[tracepoint]
pub fn enter_access(ctx: TracePointContext) -> u32 {
    match file::try_enter_access(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn enter_execve(ctx: TracePointContext) -> u32 {
    match process::try_enter_execve(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn enter_open(ctx: TracePointContext) -> u32 {
    match file::try_enter_open(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn exit_open(ctx: TracePointContext) -> u32 {
    match file::try_exit_open(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn enter_openat(ctx: TracePointContext) -> u32 {
    match file::try_enter_openat(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn exit_openat(ctx: TracePointContext) -> u32 {
    match file::try_exit_openat(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn enter_openat2(ctx: TracePointContext) -> u32 {
    match file::try_enter_openat2(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn enter_write(ctx: TracePointContext) -> u32 {
    match file::try_enter_write(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[tracepoint]
pub fn enter_read(ctx: TracePointContext) -> u32 {
    match file::try_enter_read(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
