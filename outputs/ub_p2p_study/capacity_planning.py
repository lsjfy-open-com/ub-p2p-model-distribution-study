"""Analytic capacity sensitivity only; NOT a UB/power/SSD hardware simulation.
Units: decimal GB, GB/s, s. Shared budget is already reserved for distribution.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
rows=[]
for n in (10,50,100,200):
 for budget in (4.,10.,40.,100.):
  for sink in (1.,4.):
   s=140.; deadline=300.
   bound=max(n*s/budget,s/sink)
   rows.append(dict(nodes=n,model_gb=s,distribution_budget_GBps=budget,
                    effective_receiver_GBps=sink,lower_bound_s=bound,
                    deadline_s=deadline,necessary_conditions_met=bound<=deadline,
                    source_limited_max_nodes=int(budget*deadline/s),
                    per_node_fair_GBps=min(budget/n,sink)))
assert max(50*140/40,140/4)==175
assert int(40*300/140)==85
assert max(50*140/4,140/4)==1750
out=dict(kind='Analytical necessary conditions, not simulated completion or hardware data',
         assumptions=['no existing local chunks; each receiver needs full 140 GB',
                      'effective shared budget includes source and fabric constraints',
                      'receiver budget includes network and sustained SSD constraints',
                      'ignores startup, tail, hash, flush latency and model loading'],rows=rows,
         illustrative_memory=dict(host_GiB=512,store_GiB=320,services_GiB=96,
             reserve_GiB=48,unallocated_GiB=48,full_model_140GB_GiB=140e9/2**30,
             four_64MiB_double_buffers_GiB=4*2*64/1024))
(ROOT/'capacity_planning.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS: 64 analytical scenarios; 3 arithmetic checks; no hardware or power curve inferred')
