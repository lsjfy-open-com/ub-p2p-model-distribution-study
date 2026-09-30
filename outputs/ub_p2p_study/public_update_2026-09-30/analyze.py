"""Reproducible sensitivity analysis; no UB hardware performance claims.

Reuses the existing fluid scheduler, preserves historical simulation outputs.
GB/s and GB use decimal units. Endpoint and fabric budgets are assumptions.
"""
from pathlib import Path
import json
import math
import sys
import csv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from simulator import Config, simulate

SIZE = 140.0
scenarios = [
    ('U50_C8_F2000', 50, 8, 286.72, 2000),
    ('U200_C8_F2000', 200, 8, 286.72, 2000),
    ('U1000_C8_F2000', 1000, 8, 286.72, 2000),
    ('U1000_C16_F2000', 1000, 16, 573.44, 2000),
    ('fabric_constrained', 200, 8, 286.72, 50),
    ('service_reserves_dram', 200, 8, 30, 2000),
]
results = []
for name, endpoint, channels, memory, fabric in scenarios:
    for n in (50, 100):
        methods = [('single', n), ('p2p', 1)]
        if name.startswith('U'):
            methods.append(('p2p', n))
        for policy, window in methods:
            config = Config(n=n, size_gb=SIZE, chunk_gb=.25, policy=policy,
                source_gbps=endpoint, down_gbps=endpoint, peer_up_gbps=endpoint,
                source_memory_gbps=memory, memory_gbps=memory,
                fabric_gbps=fabric, slots=window, hop_delay_s=.00002)
            result = simulate(config)
            bound = max(n*SIZE/min(endpoint, memory), SIZE/min(endpoint, memory), n*SIZE/fabric) if policy == 'single' else max(SIZE/min(endpoint, memory), 2*SIZE/memory, n*SIZE/fabric)
            assert result['time_s'] + 1e-6 >= bound
            assert math.isclose(result['source_gb'] + result['peer_gb'], n*SIZE, rel_tol=1e-8)
            result.update(scenario=name, channels=channels, lower_bound_with_memory_s=bound,
                model='chunk_fluid_not_hardware', memory_ready='complete_local_DRAM',
                modeled_cluster_dram_read_and_write_GB=2*n*SIZE)
            results.append(result)
            print(name, n, policy, window, round(result['time_s'], 4), flush=True)

analytic = []
for channels in (8, 12, 16):
    peak = channels*6400*8/1000
    dram = .7*peak
    for endpoint in (50, 200, 1000):
        for n in (1, 8, 16, 32, 50, 100):
            source = min(endpoint, dram)
            analytic.append(dict(channels=channels, rate_MT_s=6400,
                dram_peak_GB_s=peak, assumed_available_GB_s=dram,
                endpoint_payload_GB_s=endpoint, receivers=n,
                source_payload_GB_s=source, direct_resource_lower_s=n*SIZE/source,
                n_max_10s=math.floor(source*10/SIZE),
                n_max_30s=math.floor(source*30/SIZE),
                modeled_source_network_GB=n*SIZE,
                modeled_source_dram_read_GB=n*SIZE))

out = dict(assumptions=dict(size_GB=SIZE, mt_s=6400, illustrative_efficiency=.7,
    chunk_GB=.25, publish_delay_s=.00002, local_dram_ready=True,
    source_preheated=True, multicast=False, source_cache_reuse=False,
    retries=False, extra_copy=False, hash_time=False, ssd=False,
    memory_read_write_budget_is_shared=True,
    fabric_budget_counts_each_endpoint_transfer_once_not_each_switch_hop=True,
    dram_budget_30_is_hypothetical_service_remaining_budget=True,
    all_budgets_are_sensitivity_inputs_not_product_specs=True),
    analytic=analytic, simulations=results)
(ROOT/'results.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
keys=['scenario','n','policy','slots','time_s','lower_bound_with_memory_s','source_gb','peer_gb','peak_total_gbps','modeled_cluster_dram_read_and_write_GB']
with (ROOT/'results.csv').open('w', newline='') as f:
    writer=csv.DictWriter(f, fieldnames=keys, extrasaction='ignore', lineterminator='\n')
    writer.writeheader();writer.writerows(results)

from plot_sensitivity import draw
draw(results, ROOT)

print('Saved',len(analytic),'analytic rows and',len(results),'scheduler simulations',flush=True)
