"""Homogeneous UB endpoints: analytic bounds and chunk-fluid simulations.
All bandwidths are decimal GB/s. Parameters are scenarios, not product specs.
Does not modify the historical results.json. Run from any working directory.
"""
from pathlib import Path
import json, math
from simulator import Config, simulate

ROOT = Path(__file__).resolve().parent
S, RATE, EFF, FABRIC = 140.0, 6400, 0.70, 20000.0

def main():
    bounds, runs = [], []
    for channels in (8, 12, 16):
        peak = channels * RATE * 8 / 1000
        dram = peak * EFF
        for ub in (200.0, 1000.0):
            source = min(ub, dram)
            for n in (1, 10, 50, 100, 200):
                direct = max(n*S/source, n*S/FABRIC, S/min(ub, dram))
                # For N>=2 an interior relay receives and forwards a full package.
                p2p = max(S/source, n*S/FABRIC, (2 if n > 1 else 1)*S/dram)
                bounds.append(dict(receivers=n, channels=channels, mt_s=RATE,
                    dram_peak_GB_s=peak, dram_budget_GB_s=dram, endpoint_GB_s=ub,
                    direct_lower_s=direct, chain_lower_s=p2p,
                    direct_ssd4_lower_s=max(direct,S/4),
                    chain_ssd4_lower_s=max(p2p,S/4),
                    n_max_10s=math.floor(source*10/S),
                    n_max_30s=math.floor(source*30/S)))
    for channels in (8, 16):
        dram = channels * RATE * 8 / 1000 * EFF
        for ub in (200.0, 1000.0):
            for n in (10, 50, 100):
                for policy, slots in (('single', n), ('p2p', n), ('p2p', 1)):
                    config = Config(n=n, size_gb=S, chunk_gb=.25, policy=policy,
                        source_gbps=ub, down_gbps=ub, peer_up_gbps=ub,
                        source_memory_gbps=dram, memory_gbps=dram,
                        fabric_gbps=FABRIC, slots=slots, hop_delay_s=.00002)
                    result = simulate(config)
                    result.update(channels=channels, mt_s=RATE, efficiency=EFF)
                    # Traffic accounting and analytic lower bounds, independent of scheduling.
                    expect_source = S*n if policy == 'single' else S
                    assert math.isclose(result['source_gb'],expect_source,rel_tol=1e-8)
                    assert math.isclose(result['source_gb']+result['peer_gb'],S*n,rel_tol=1e-8)
                    bound = next(b for b in bounds if b['channels']==channels and b['endpoint_GB_s']==ub and b['receivers']==n)
                    lower = bound['direct_lower_s' if policy=='single' else 'chain_lower_s']
                    assert result['time_s'] >= lower-1e-6
                    runs.append(result)
                    print(channels,ub,n,policy,slots,round(result['time_s'],4),flush=True)
    out = dict(assumptions=dict(size_GB=S, mt_s=RATE, efficiency=EFF,
        fabric_GB_s=FABRIC, receive_dram_bytes_per_payload_byte=1,
        send_dram_bytes_per_payload_byte=1, source_hot=True,
        includes_ssd_simulation=False, includes_hardware_measurement=False),
        bounds=bounds, simulations=runs)
    (ROOT/'memory_scale_results.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__ == '__main__':
    main()
