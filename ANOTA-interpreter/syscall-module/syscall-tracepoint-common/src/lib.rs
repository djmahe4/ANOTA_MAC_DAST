#![no_std]
use bytemuck::{Pod, Zeroable};

pub const MAX_PATH: usize = 4096;

#[repr(C)]
#[derive(Clone, Copy, Zeroable, Pod)]
pub struct Buf {
    pub buf: [u8; MAX_PATH],
}

#[repr(C)]
#[derive(Clone, Copy, Default, Zeroable, Pod)]
pub struct WatchConfig {
    pub enabled: u32,
    pub target_pid: u32,
}

#[cfg(feature = "user")]
unsafe impl aya::Pod for Buf {}

#[cfg(feature = "user")]
unsafe impl aya::Pod for WatchConfig {}

#[cfg(not(feature = "user"))]
use aya_ebpf::maps::{PerCpuArray, Array};
#[cfg(not(feature = "user"))]
use aya_ebpf::macros::map;

#[cfg(not(feature = "user"))]
#[map]
pub static BUF: PerCpuArray<Buf> = PerCpuArray::with_max_entries(1, 0);

#[cfg(not(feature = "user"))]
#[map]
pub static WATCH_CONFIG: Array<WatchConfig> = Array::with_max_entries(1, 0);
