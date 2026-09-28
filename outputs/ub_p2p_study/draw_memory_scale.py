"""Render new memory-scale results and refresh the report's simulation table."""
from pathlib import Path
import json,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'memory_scale_results.json').read_text())['simulations']
def result(c,u,n,p,w):
    return next(r for r in rows if r['channels']==c and r['source_gbps']==u and r['n']==n and r['policy']==p and r['slots']==w)
lines=['|C|U GB/s|N|纯 UB W=N 秒|P2P W=N 秒|P2P W=1 秒|',
       '|---|---:|---:|---:|---:|---:|']
for c in (8,16):
 for u in (200,1000):
  for n in (10,50,100):
   vals=[result(c,u,n,p,w)['time_s'] for p,w in [('single',n),('p2p',n),('p2p',1)]]
   lines.append('|'+ '|'.join([str(c),str(u),str(n)]+[f'{v:.3f}' for v in vals])+'|')
p=ROOT/'ub_memory_scale_assessment.md'
s=p.read_text()
block='<!-- SIMULATION_TABLE -->\n'+ '\n'.join(lines)+'\n<!-- END_SIMULATION_TABLE -->'
s=re.sub(r'<!-- SIMULATION_TABLE -->(?:.*?<!-- END_SIMULATION_TABLE -->)?',lambda _:block,s,flags=re.S)
p.write_text(s)
fig,axes=plt.subplots(1,2,figsize=(11.5,4.9),sharey=True)
for ax,u in zip(axes,(200,1000)):
 for p,mode,label,color in [('single','wide','Direct UB, W=N','#264d73'),('p2p','wide','P2P chain, W=N','#b36d22'),('p2p','one','P2P chain, W=1','#138878')]:
  ns=[10,50,100]
  ys=[result(8,u,n,p,n if mode=='wide' else 1)['time_s'] for n in ns]
  ax.plot(ns,ys,'o-',label=label,color=color,lw=2)
 ax.set_title(f'Each endpoint U = {u} GB/s')
 ax.set_xlabel('Receiving nodes N (OM additional)')
 ax.set_xticks([10,50,100]);ax.grid(alpha=.2);ax.set_ylim(0,75)
axes[0].set_ylabel('All receivers complete (seconds)')
axes[1].legend(loc='upper left',frameon=False,fontsize=9)
fig.suptitle('Homogeneous endpoints: model distribution to DRAM',fontsize=15)
fig.text(.5,.015,'140 GB; 8 x DDR5-6400; DRAM budget 286.72 GB/s; fabric 20,000 GB/s. Simulation, not hardware measurement.',ha='center',fontsize=8)
fig.tight_layout(rect=(0,.06,1,.95))
fig.savefig(ROOT/'figures/memory_scale_comparison.png',dpi=180)
fig.savefig(ROOT/'figures/memory_scale_comparison.svg')
plt.close(fig)
