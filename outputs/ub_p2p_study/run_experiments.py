"""Run scenarios, write every configuration/result, create publication plots.
Usage: python run_experiments.py --workers 4
"""
from dataclasses import replace
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse, csv, json, sys, time, platform
from simulator import Config, simulate

ROOT = Path(__file__).resolve().parent


def scenarios():
    base = Config()
    jobs = []
    def add(group, label, c):
        jobs.append((group,label,c))
    for bw in [10.,40.]:
        for n in [1,8,16,32,50,100]:
            for policy,k in [("single",1),("multi",4),("multi",8),("p2p",1)]:
                # prevent supplying more seed machines than receiving clients
                if k>n: continue
                add("scale",f"B{bw:g}_N{n}_{policy}{k}",replace(base,n=n,
                    source_gbps=bw,down_gbps=bw,peer_up_gbps=bw,policy=policy,seeds=k))
    cases = {
        "fabric_10": dict(fabric_gbps=10.),
        "fabric_100": dict(fabric_gbps=100.),
        "fabric_400": dict(fabric_gbps=400.),
        "sink_1": dict(sink_gbps=1.),
        "memory_10": dict(memory_gbps=10.),
        "peer_upload_1": dict(peer_up_gbps=1.),
        "slow_peer_0.1": dict(slow_factor=.1),
        "fast_source_200": dict(source_gbps=200.,slots=100),
        "rack_2_local": dict(rack_gbps=2.),
        "rack_2_random": dict(rack_gbps=2.,ordering="random",random_seed=42),
    }
    for name,kw in cases.items():
        for policy in ["single","p2p"]:
            add("limits",name+"_"+policy,replace(base,policy=policy,**kw))
        wide=dict(kw);wide['slots']=100
        add("limits_wide",name+"_single_wide",replace(base,policy="single",**wide))
    # Chunk convergence and source fanout; all physical quantities unchanged.
    for chunk in [.015625,.0625,.25,1.,4.,140.]:
        add("chunks",f"chunk_{chunk:g}",replace(base,chunk_gb=chunk))
    for slots in [1,4,16]:
        add("slots",f"slots_{slots}",replace(base,slots=slots))
    for delay in [0.,.00002,.001,.01]:
        add("delay",f"delay_{delay:g}",replace(base,hop_delay_s=delay))
    # Source sensitivity: payload budgets, NOT claimed UB device specifications.
    for bw in [5.,10.,21.25,40.,80.,200.]:
        for policy in ["single","p2p"]:
            add("source",f"source_{bw:g}_{policy}",replace(base,policy=policy,
                source_gbps=bw,slots=100))
        add("source_tuned",f"source_{bw:g}_p2p_window1",replace(base,source_gbps=bw))
    add("counterexample","source200_peer1_p2p",replace(base,source_gbps=200.,peer_up_gbps=1.))
    add("counterexample","source2000_single",replace(base,source_gbps=2000.,slots=100,policy="single"))
    add("counterexample","source2000_p2p",replace(base,source_gbps=2000.))
    # Random topology variation is not real-machine measurement uncertainty.
    for seed in range(5):
        add("topology",f"random_{seed}",replace(base,rack_gbps=2.,ordering="random",random_seed=seed))
    add("policy","rotating_slots4",replace(base,root_mode="rotating",slots=4,chunk_gb=1.))
    for size in [14.,70.,140.,280.]:
        for policy in ["single","p2p"]:
            add("size",f"size_{size:g}_{policy}",replace(base,size_gb=size,policy=policy))
    return jobs


def execute(job):
    group,label,c=job
    t=time.monotonic()
    r=simulate(c)
    return dict(group=group,label=label,**r,wall_seconds=time.monotonic()-t)


def plots(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
                         "figure.dpi":150,"savefig.dpi":170})
    fig,axs=plt.subplots(1,2,figsize=(12,4.4),layout="constrained")
    colors=["#52606d","#2f80ed","#7b61a8","#009a83"]
    for ax,bw in zip(axs,[10.,40.]):
        for (p,k),color in zip([("single",1),("multi",4),("multi",8),("p2p",1)],colors):
            rr=sorted([r for r in rows if r["group"]=="scale" and r["source_gbps"]==bw
                       and r["policy"]==p and r["seeds"]==k],key=lambda r:r["n"])
            label={"single":"Single source","multi":f"{k} preloaded seeds","p2p":"P2P pipeline"}[p]
            ax.plot([r["n"] for r in rr],[r["time_s"] for r in rr],"o-",label=label,color=color)
        ax.set(title=f"Effective endpoint budget: {bw:g} GB/s (assumed)",xlabel="Empty receiving nodes",ylabel="All nodes data-ready (s)",yscale="log")
        ax.grid(alpha=.2); ax.legend(fontsize=8)
    fig.suptitle("140 GB per node | warm source | 250 MB chunks | simulation, not hardware results")
    fig.savefig(ROOT/"figures/scaling.png"); plt.close(fig)

    names=["fabric_10","fabric_100","sink_1","memory_10","peer_upload_1","slow_peer_0.1","fast_source_200","rack_2_local","rack_2_random"]
    fig,ax=plt.subplots(figsize=(12,5),layout="constrained")
    yy=np.arange(len(names))
    for offset,p,color in [(-.18,"single",colors[0]),(.18,"p2p",colors[3])]:
        labels_available={r['label']:r for r in rows}
        values=[labels_available.get(name+"_single_wide",labels_available[name+"_single"])["time_s"]
                if p=="single" else labels_available[name+"_p2p"]["time_s"] for name in names]
        bars=ax.barh(yy+offset,values,height=.35,label=p,color=color)
        ax.bar_label(bars,fmt="%.1f",padding=3,fontsize=8)
    ax.set(yticks=yy,yticklabels=names,xscale="log",xlabel="All nodes data-ready (s), log scale",
           title="Bottlenecks | N=100, S=140 GB | single-source window=100")
    ax.invert_yaxis();ax.legend();ax.grid(axis="x",alpha=.2)
    fig.savefig(ROOT/"figures/bottlenecks.png");plt.close(fig)

    rr=sorted([r for r in rows if r["group"]=="chunks"],key=lambda r:r["chunk_gb"])
    fig,axs=plt.subplots(1,2,figsize=(12,4.4),layout="constrained")
    axs[0].plot([r["chunk_gb"]*1000 for r in rr],[r["time_s"] for r in rr],"o-",color=colors[3])
    axs[0].axhline(14,color=colors[0],ls="--",label="Fluid lower bound: 14 s")
    axs[0].set(xscale="log",yscale="log",xlabel="Chunk size (decimal MB)",ylabel="Data-ready (s)",title="Pipeline fill/drain penalty")
    axs[0].legend();axs[0].grid(alpha=.2)
    src=sorted([r for r in rows if r["group"]=="source" and r["policy"]=="single"],key=lambda r:r["source_gbps"])
    p2p=sorted([r for r in rows if r["group"]=="source" and r["policy"]=="p2p"],key=lambda r:r["source_gbps"])
    axs[1].plot([r["source_gbps"] for r in src],[r["time_s"] for r in src],"o-",label="Single",color=colors[0])
    axs[1].plot([r["source_gbps"] for r in p2p],[r["time_s"] for r in p2p],"o-",label="P2P, FIFO window=100",color=colors[3])
    tuned=sorted([r for r in rows if r["group"]=="source_tuned"],key=lambda r:r["source_gbps"])
    if tuned:
        axs[1].plot([r["source_gbps"] for r in tuned],[r["time_s"] for r in tuned],"s--",label="P2P, window=1",color=colors[1])
    axs[1].set(xscale="log",yscale="log",xlabel="Source payload budget (GB/s)",ylabel="Data-ready (s)",title="Source bandwidth sensitivity; peers fixed at 10 GB/s")
    axs[1].legend();axs[1].grid(alpha=.2)
    fig.savefig(ROOT/"figures/sensitivity.png");plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(12,4.2),layout="constrained")
    rr=[next(r for r in rows if r["label"]==f"B10_N100_{p}{k}") for p,k in [("single",1),("multi",4),("multi",8),("p2p",1)]]
    labels=["Single","4 seeds","8 seeds","P2P"]
    axs[0].bar(labels,[r["source_gb"] for r in rr],label="Seed egress",color=colors[0])
    axs[0].bar(labels,[r["peer_gb"] for r in rr],bottom=[r["source_gb"] for r in rr],label="Peer egress",color=colors[3])
    axs[0].set(ylabel="Logical transferred GB",title="Same 14,000 GB total; different senders")
    axs[0].legend()
    axs[1].bar(labels,[r["peak_total_gbps"] for r in rr],color=colors)
    axs[1].set(ylabel="Aggregate logical payload GB/s",title="P2P can INCREASE aggregate instantaneous load")
    fig.savefig(ROOT/"figures/traffic.png");plt.close(fig)


def main():
    p=argparse.ArgumentParser();p.add_argument("--workers",type=int,default=4)
    p.add_argument("--resume",action="store_true")
    p.add_argument("--plots-only",action="store_true");a=p.parse_args()
    (ROOT/"figures").mkdir(exist_ok=True)
    if a.plots_only:
        plots(json.loads((ROOT/"results.json").read_text()));return
    jobs=scenarios();results=[]
    if a.resume and (ROOT/"results.json").exists():
        results=json.loads((ROOT/"results.json").read_text())
        done={r["label"] for r in results}
        jobs=[j for j in jobs if j[1] not in done]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(execute,j):j for j in jobs}
        for i,f in enumerate(as_completed(futures),1):
            r=f.result();results.append(r)
            print(f"{i}/{len(jobs)} {r['label']}: {r['time_s']:.4f}s (wall {r['wall_seconds']:.1f}s)",flush=True)
            (ROOT/"results.partial.json").write_text(json.dumps(results,indent=2))
    results.sort(key=lambda r:(r["group"],r["label"]))
    (ROOT/"results.json").write_text(json.dumps(results,indent=2))
    with (ROOT/"results.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=results[0].keys());w.writeheader();w.writerows(results)
    import numpy
    (ROOT/"environment.json").write_text(json.dumps(dict(python=sys.version,
        platform=platform.platform(),numpy=numpy.__version__,scenarios=len(results)),indent=2))
    plots(results)

if __name__=="__main__":main()
