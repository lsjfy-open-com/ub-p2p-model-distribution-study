"""Deterministic, chunk-level fluid discrete-event model. Units: GB, GB/s, s.

Not a UB/TCP protocol emulator. No hardware performance is claimed.
P2P policy: each chunk is injected once, then follows a Hamiltonian path
through all clients (fixed pipeline by default, optional rotating roots).
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import deque
import heapq
import math
import numpy as np


@dataclass
class Config:
    n: int = 100                    # empty clients; seed machines are additional
    size_gb: float = 140.0
    chunk_gb: float = 0.25          # decimal GB, NOT GiB
    policy: str = "p2p"           # single, multi, p2p
    seeds: int = 1
    source_gbps: float = 10.0      # effective payload GB/s per seed
    down_gbps: float = 10.0
    peer_up_gbps: float = 10.0
    sink_gbps: float = 1e9         # streaming sink throughput, not fsync model
    memory_gbps: float = 1e9       # shared client receive+send payload budget
    fabric_gbps: float = 1e9       # global transfer-byte capacity; counts once
    rack_gbps: float = 1e9         # each rack's directional cross-rack capacity
    rack_size: int = 10
    ordering: str = "local"       # local or random
    hop_delay_s: float = 0.00002   # publication/propagation delay, parallelizable
    slots: int = 1                # active outgoing chunks per sender
    root_mode: str = "fixed"     # fixed pipeline chain or rotating chunk roots
    random_seed: int = 0
    slow_factor: float = 1.0       # client 0 upload & download multiplier
    source_memory_gbps: float = 1e9


def validate_config(c):
    """Reject invalid budgets before constructing a simulation."""
    for key in ("n", "seeds", "slots", "rack_size"):
        value = getattr(c, key)
        if type(value) is not int or value < 1:
            raise ValueError(f"{key} must be a positive integer")
    if type(c.random_seed) is not int or c.random_seed < 0:
        raise ValueError("random_seed must be a nonnegative integer")
    for key in ("size_gb", "chunk_gb", "source_gbps", "down_gbps", "peer_up_gbps",
                "sink_gbps", "memory_gbps", "fabric_gbps", "rack_gbps",
                "slow_factor", "source_memory_gbps"):
        value = getattr(c, key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{key} must be finite and positive")
    if not isinstance(c.hop_delay_s, (int, float)) or not math.isfinite(c.hop_delay_s) or c.hop_delay_s < 0:
        raise ValueError("hop_delay_s must be finite and nonnegative")
    for key, choices in (("policy", {"single", "multi", "p2p"}),
                         ("ordering", {"local", "random"}),
                         ("root_mode", {"fixed", "rotating"})):
        if getattr(c, key) not in choices:
            raise ValueError(f"unsupported {key}: {getattr(c, key)}")


def max_min_rates(resource_lists, capacities):
    """Progressive filling: max-min fair rates over fixed active flow routes.

    Every flow consumes one unit on each of its listed resources. Resources
    include source upload, destination download, shared memory and rack cuts.
    """
    m = len(resource_lists)
    row = np.concatenate([np.asarray(r, dtype=int) for r in resource_lists])
    col = np.repeat(np.arange(m), [len(r) for r in resource_lists])
    rates = np.zeros(m)
    free = np.ones(m, dtype=bool)
    residual = capacities.copy()
    while free.any():
        mask = free[col]
        counts = np.bincount(row[mask], minlength=len(capacities))
        ratios = np.full(len(capacities), np.inf)
        np.divide(np.maximum(residual, 0), counts, out=ratios, where=counts > 0)
        delta = ratios.min()
        rates[free] += delta
        residual -= delta * counts
        tight = (counts > 0) & (ratios <= delta + 1e-10 * max(1., delta))
        blocked = np.unique(col[mask & tight[row]])
        assert len(blocked), "progressive filling must make progress"
        free[blocked] = False
    load = np.bincount(row, weights=rates[col], minlength=len(capacities))
    assert np.all(load <= capacities + 1e-7 * np.maximum(1, capacities))
    return rates


def simulate(c: Config, trace=False):
    validate_config(c)
    k = c.seeds if c.policy == "multi" else 1
    total = k + c.n
    chunks = math.ceil(c.size_gb / c.chunk_gb)
    sizes = np.minimum(c.chunk_gb, c.size_gb - np.arange(chunks) * c.chunk_gb)
    order = np.arange(c.n)
    if c.ordering == "random":
        np.random.default_rng(c.random_seed).shuffle(order)
    position = np.empty(c.n, dtype=int)
    position[order] = np.arange(c.n)
    # seeds share rack 0; each group of clients occupies rack 1,2,...
    racks = [0] * k + [1 + i // c.rack_size for i in range(c.n)]
    nracks = max(racks) + 1
    up = np.array([min(c.source_gbps, c.source_memory_gbps)] * k +
                  [c.peer_up_gbps] * c.n)
    down = np.array([c.down_gbps] * k + [min(c.down_gbps, c.sink_gbps)] * c.n)
    up[k] *= c.slow_factor
    down[k] = min(c.down_gbps * c.slow_factor, c.sink_gbps)
    mem = np.array([c.source_memory_gbps] * k + [c.memory_gbps] * c.n)
    caps = np.concatenate([up, down, mem, [c.fabric_gbps],
                           [c.rack_gbps] * (2 * nracks)])
    fabric_idx = 3 * total
    rack_start = fabric_idx + 1
    resources = {}

    def route(src, dst):
        key = (src, dst)
        if key not in resources:
            rr = [src, total + dst, 2 * total + src, 2 * total + dst, fabric_idx]
            if racks[src] != racks[dst]:
                rr += [rack_start + racks[src], rack_start + nracks + racks[dst]]
            resources[key] = rr
        return resources[key]

    # Job = (src, dst, chunk, number of clients still to visit after dst)
    queues = [deque() for _ in range(total)]
    if c.policy == "p2p":
        for ch in range(chunks):
            root = ch % c.n if c.root_mode == "rotating" else 0
            queues[0].append((0, k + int(order[root]), ch, c.n - 1))
    else:
        # chunk-major ordering prevents one client's entire file going first
        for ch in range(chunks):
            for i in range(c.n):
                src = i % k
                queues[src].append((src, k + i, ch, 0))

    active = []                   # [job, remaining GB]
    occupancy = np.zeros(total, dtype=int)
    delayed = []                  # ready-time, unique sequence, completed job
    sequence = 0
    received = np.zeros((c.n, chunks), dtype=bool)
    received_counts = np.zeros(c.n, dtype=int)
    finished = np.full(c.n, np.nan)
    time_s = 0.
    source_bytes = peer_bytes = cross_bytes = 0.
    peak_source = peak_total = 0.
    events = 0
    timeline = []

    def publish(job):
        src, dst, ch, remaining = job
        i = dst - k
        assert not received[i, ch], "duplicate delivery"
        received[i, ch] = True
        received_counts[i] += 1
        if received_counts[i] == chunks:
            finished[i] = time_s
        if remaining:
            nxt = int(order[(position[i] + 1) % c.n])
            queues[dst].append((dst, k + nxt, ch, remaining - 1))

    while np.isnan(finished).any():
        while delayed and delayed[0][0] <= time_s + 1e-10:
            _, _, job = heapq.heappop(delayed)
            publish(job)
        for src in range(total):
            while queues[src] and occupancy[src] < c.slots:
                job = queues[src].popleft()
                if src >= k:
                    assert received[src-k, job[2]], "forward before complete"
                active.append([job, float(sizes[job[2]])])
                occupancy[src] += 1
        if not active:
            if delayed:
                time_s = delayed[0][0]
                continue
            assert not np.isnan(finished).any(), "deadlock"
            break
        rates = max_min_rates([route(a[0][0], a[0][1]) for a in active], caps)
        dt = min(a[1] / r for a, r in zip(active, rates))
        if delayed:
            dt = min(dt, max(0., delayed[0][0] - time_s))
        assert dt >= 0
        source_rate = sum(r for a, r in zip(active, rates) if a[0][0] < k)
        peak_source = max(peak_source, source_rate)
        peak_total = max(peak_total, rates.sum())
        if trace:
            timeline.append([time_s, time_s+dt, source_rate, float(rates.sum()),
                             int(np.count_nonzero(~np.isnan(finished)))])
        for a, r in zip(active, rates):
            moved = min(a[1], r * dt)
            a[1] -= moved
            src, dst, _, _ = a[0]
            if src < k:
                source_bytes += moved
            else:
                peer_bytes += moved
            if racks[src] != racks[dst]:
                cross_bytes += moved
        time_s += dt
        remaining_active = []
        for a in active:
            if a[1] <= 1e-8:
                job = a[0]
                occupancy[job[0]] -= 1
                sequence += 1
                heapq.heappush(delayed, (time_s+c.hop_delay_s, sequence, job))
            else:
                remaining_active.append(a)
        active = remaining_active
        events += 1
        assert events < 10_000_000, "event limit"
    assert received.all()
    expected = c.size_gb * c.n
    assert math.isclose(source_bytes + peer_bytes, expected, rel_tol=1e-7)
    expected_source = c.size_gb if c.policy == "p2p" else expected
    assert math.isclose(source_bytes, expected_source, rel_tol=1e-7)
    min_down = min(down[k:])
    if c.policy == "p2p":
        lower = max(c.size_gb / up[0], c.size_gb / min_down,
                    expected / (up[0] + sum(up[k:])), expected / c.fabric_gbps)
    else:
        lower = max(expected / sum(up[:k]), c.size_gb / min_down,
                    expected / c.fabric_gbps)
    assert time_s + 1e-6 >= lower
    result = asdict(c)
    result.update(time_s=float(time_s), p50_s=float(np.percentile(finished, 50)),
                  p95_s=float(np.percentile(finished, 95)),
                  min_s=float(min(finished)), lower_bound_s=float(lower),
                  source_gb=float(source_bytes), peer_gb=float(peer_bytes),
                  cross_rack_gb=float(cross_bytes), peak_source_gbps=float(peak_source),
                  peak_total_gbps=float(peak_total), events=events,
                  chunks=chunks, final_client_cache_gb=expected)
    if trace:
        result["timeline"] = timeline
    return result


if __name__ == "__main__":
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument("--config", help="JSON object matching Config")
    p.add_argument("--output")
    a = p.parse_args()
    c = Config(**json.load(open(a.config))) if a.config else Config()
    text = json.dumps(simulate(c), indent=2)
    if a.output:
        open(a.output, "w").write(text + "\n")
    else:
        print(text)
