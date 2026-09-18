"""Audit historical records without overwriting them; rerun representative cases."""
from pathlib import Path
from dataclasses import fields
from collections import defaultdict
import hashlib, json, math
from simulator import Config, simulate
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'results.json').read_text())
keys=[f.name for f in fields(Config)]
groups=defaultdict(list)
for r in rows:
    groups[json.dumps({k:r[k] for k in keys},sort_keys=True)].append(r['label'])
    assert math.isclose(r['source_gb']+r['peer_gb'],r['n']*r['size_gb'],rel_tol=1e-8)
    assert math.isclose(r['final_client_cache_gb'],r['n']*r['size_gb'],rel_tol=1e-8)
    if r['policy']=='p2p':
        assert math.isclose(r['source_gb'],r['size_gb'],rel_tol=1e-8)
by={r['label']:r for r in rows}
checks=[]
for label in ['B10_N50_p2p1','B10_N100_p2p1','B40_N100_p2p1']:
    r=by[label];m=r['size_gb']/r['chunk_gb']
    expected=(m+r['n']-1)*r['chunk_gb']/r['source_gbps']+r['n']*r['hop_delay_s']
    assert math.isclose(r['time_s'],expected,rel_tol=1e-8)
    checks.append(dict(label=label,expected_s=expected,recorded_s=r['time_s']))
reruns=[]
for label in ['B10_N100_p2p1','fabric_10_p2p','source_200_single','source200_peer1_p2p']:
    r=by[label];fresh=simulate(Config(**{k:r[k] for k in keys}))
    for k in ['time_s','source_gb','peer_gb','final_client_cache_gb','cross_rack_gb']:
        assert math.isclose(fresh[k],r[k],rel_tol=1e-8,abs_tol=1e-8),(label,k,fresh[k],r[k])
    reruns.append(dict(label=label,time_s=fresh['time_s'],matches_history=True))
    print('Recomputed',label,fresh['time_s'],flush=True)
output=dict(records=len(rows),unique_configurations=len(groups),
    duplicate_groups=[v for v in groups.values() if len(v)>1],
    byte_accounting_checked_records=len(rows), byte_accounting_relative_tolerance=1e-8,
    max_byte_accounting_relative_error=max(abs((r["source_gb"]+r["peer_gb"])/(r["n"]*r["size_gb"])-1) for r in rows),closed_form_checks=checks,representative_reruns=reruns,
    source_data_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['results.json','results.csv']},
    simulator_sha256=hashlib.sha256((ROOT/'simulator.py').read_bytes()).hexdigest(),
    disclaimer='Resource/scheduling simulation only; no TCP/UB/Ascend hardware execution.')
(ROOT/'audit_metrics.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
print('PASS:',len(rows),'records;',len(groups),'unique configurations; byte accounting, 3 closed forms, 4 reruns')
