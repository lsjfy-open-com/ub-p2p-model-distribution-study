"""Draw existing results with explicit endpoint bandwidth units."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def draw(results, root):
    scenarios=list(dict.fromkeys(r['scenario'] for r in results))
    first=[next(r for r in results if r['scenario']==name) for name in scenarios]
    labels=[f"UB {r['source_gbps']:g} GB/s\nDRAM {r['source_memory_gbps']:g} GB/s\nFabric {r['fabric_gbps']:g} GB/s" for r in first]
    fig,axes=plt.subplots(1,2,figsize=(16,6),sharey=True)
    for ax,n in zip(axes,(50,100)):
        for offset,policy,window,label,color in [(-.18,'single',n,'Direct, W=N','#477b9e'),(.18,'p2p',1,'Chain, W=1','#218778')]:
            selected=[next(r for r in results if r['scenario']==name and r['n']==n and r['policy']==policy and r['slots']==window) for name in scenarios]
            ax.bar([i+offset for i in range(len(labels))],[r['time_s'] for r in selected],width=.34,label=label,color=color)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels,rotation=24,ha='right',fontsize=8)
        ax.set_yscale('log');ax.set_title(f'N={n} recipient nodes; OM is additional')
        ax.grid(axis='y',alpha=.2)
        ax.set_ylabel('All local DRAM replicas ready (s, log scale)');ax.legend(fontsize=9)
    fig.suptitle('Model only: UB / DRAM / Fabric labels are GB/s budgets, not node counts',fontsize=12)
    fig.tight_layout()
    fig.savefig(root/'sensitivity.png',dpi=160)
    plt.close(fig)
