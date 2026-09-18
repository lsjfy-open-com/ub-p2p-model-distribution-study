"""Proposed local interface only. No TCP or URMA backend is implemented here.

Data can be consumed only after Fetch completion and independent chunk hash
verification. Completion is local-buffer-ready, not remote durability or ready.
"""
from dataclasses import dataclass
from typing import Protocol, Sequence

@dataclass(frozen=True)
class TransferKey:
    transfer_id: bytes
    peer_boot_id: bytes
    cache_generation: int
    local_buffer_generation: int

@dataclass(frozen=True)
class FetchCompletion:
    key: TransferKey
    bytes_received: int
    success: bool
    error_code: str

class ChunkTransport(Protocol):
    def prepare_buffer(self, capacity_bytes: int) -> object:
        """Reserve buffer and register it if needed; opaque process-local handle."""
        ...

    def fetch_chunk(self, grant: object, buffer: object, key: TransferKey) -> None:
        """Submit bounded operations; NOT a completion or hash verification."""
        ...

    def poll(self, max_completions: int) -> Sequence[FetchCompletion]:
        """Return full-chunk completion only after every sub-operation succeeds."""
        ...

    def cancel_and_drain(self, key: TransferKey, timeout_ms: int) -> bool:
        """True only if no local operation can access the buffer again.
        False requires quarantine; it NEVER means timeout makes reuse safe.
        """
        ...

    def release_buffer(self, buffer: object) -> None:
        """Precondition: all operations drained, no loader/forwarding references."""
        ...
