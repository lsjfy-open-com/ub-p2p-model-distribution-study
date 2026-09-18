"""Build report.md and a standalone offline HTML with embedded plots."""
from pathlib import Path
import json, base64, re, statistics
import markdown

ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'results.json').read_text())
by={r['label']:r for r in rows}
def f(v): return f'{v:,.3f}'
def table(headers, data):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(map(str,row))+' |' for row in data])

scale=[]
for b in (10,40):
    for n in (50,100):
        rr=[by[f'B{b}_N{n}_{p}{k}'] for p,k in [('single',1),('multi',4),('multi',8),('p2p',1)]]
        scale.append([b,n]+[f(r['time_s']) for r in rr]+[f(rr[0]['time_s']/rr[3]['time_s'])+'×'])
traffic=[]
for p,k,name in [('single',1,'单源'),('multi',4,'4 热种子'),('multi',8,'8 热种子'),('p2p',1,'固定链')]:
    r=by[f'B10_N100_{p}{k}']
    traffic.append([name]+[f(r[key]) for key in ['source_gb','peer_gb','final_client_cache_gb','peak_total_gbps']])
limit_names={'fabric_10':'共享 F=10 GB/s','fabric_100':'共享 F=100 GB/s','fabric_400':'共享 F=400 GB/s',
             'sink_1':'每客户端 sink=1 GB/s','memory_10':'DDR 收发合计 10 GB/s','peer_upload_1':'Peer 上传 1 GB/s',
             'slow_peer_0.1':'一个 Peer 收发降至 10%','fast_source_200':'源 200 GB/s；双方 W=100',
             'rack_2_local':'每架出入各 2 GB/s，同架相邻','rack_2_random':'每架出入各 2 GB/s，随机路径 42'}
limits=[]
for key,name in limit_names.items():
    a=by[key+'_single_wide'];b=by[key+'_p2p']
    limits.append([name,100 if key=='fast_source_200' else 1,f(a['time_s']),f(b['time_s']),f(a['time_s']/b['time_s'])+'×',f(b['cross_rack_gb'])])
chunks=[[f(r['chunk_gb']*1000),r['chunks'],f(r['time_s'])]
        for r in sorted(rows,key=lambda x:x['chunk_gb']) if r['group']=='chunks']
window=[[r['slots'],f(r['time_s'])] for r in sorted(rows,key=lambda x:x['slots']) if r['group']=='slots']
counter=[]
for title,a,b in [('强源 200、Peer 上传 1；单源 W=100，P2P W=1','source_200_single','source200_peer1_p2p'),
                  ('假设源 2,000、Peer 10；单源 W=100，P2P W=1','source2000_single','source2000_p2p'),
                  ('源 200、Peer 10；双方 W=100','fast_source_200_single','fast_source_200_p2p')]:
    counter.append([title,f(by[a]['time_s']),f(by[b]['time_s'])])
topo=[r['time_s'] for r in rows if r['group']=='topology']
values={
 'RUN_COUNT':str(len(rows)),
 'BASE_SINGLE':f(by['B10_N100_single1']['time_s']),
 'BASE_P2P':f(by['B10_N100_p2p1']['time_s']),
 'SCALE_TABLE':table(['带宽 GB/s','客户端数','单源秒','4 种子秒','8 种子秒','固定链秒','单源/固定链'],scale),
 'TRAFFIC_TABLE':table(['方案','种子发出 GB','Peer 发出 GB','最终客户端缓存 GB','全网瞬时载荷峰值 GB/s'],traffic),
 'LIMITS_TABLE':table(['约束','固定链 W','单源 W=100 秒','固定链秒','单源/固定链','固定链跨架 GB'],limits),
 'CHUNKS_TABLE':table(['分块 MB（十进制）','块数','固定链秒'],chunks),
 'WINDOW_TABLE':table(['每发送端活跃块 W','固定链秒'],window),
 'COUNTER_TABLE':table(['条件，带宽均 GB/s','单源秒','固定链秒'],counter),
 'TOPO_RANGE':f(min(topo))+'～'+f(max(topo)),
 'TOPO_MEAN':f(statistics.mean(topo)),
}
css='''body{max-width:1080px;margin:48px auto;padding:0 28px;font:16px/1.85 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:#182c3a;background:#fff}h1{font-size:32px;line-height:1.4}h2{margin-top:56px;border-bottom:2px solid #138878;padding-bottom:8px}h3{margin-top:30px}table{border-collapse:collapse;width:100%;font-size:14px;display:block;overflow:auto}td,th{border:1px solid #dbe3e9;padding:9px 12px;text-align:left}th{background:#edf5f4}tr:nth-child(even){background:#f7f9fa}pre{background:#f1f5f8;padding:18px;border-radius:8px;white-space:pre-wrap;overflow-wrap:anywhere}code{font-family:ui-monospace,Menlo,monospace;font-size:.9em}img{width:100%;height:auto}blockquote{margin:24px 0;padding:14px 22px;background:#fff6df;border-left:4px solid #bc8a26}a{color:#087b73}p,li{overflow-wrap:anywhere}@media print{body{margin:0;max-width:none;font-size:10pt}h2{margin-top:24px;break-after:avoid}h3{break-after:avoid}table{font-size:8pt;display:table}pre{font-size:8pt}img{max-height:210mm;object-fit:contain}tr{break-inside:avoid}a{color:inherit}}'''

def embed(match):
    path=ROOT/match.group(1)
    return 'src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"'

def render(name, template=False):
    source = ROOT / (name + ('_template.md' if template else '.md'))
    body = source.read_text()
    for key, value in values.items():
        body = body.replace('{{'+key+'}}', value)
    assert '{{' not in body
    if template:
        (ROOT/(name+'.md')).write_text(body)
    html = markdown.markdown(body, extensions=['tables','fenced_code','toc'])
    html = re.sub(r'src="(figures/[^\"]+\.png)"', embed, html)
    for target in ('report','experiment_details','protocol_design','audit_review','baseline_protocol'):
        html = html.replace('href="'+target+'.md"', 'href="'+target+'.html"')
    title = body.splitlines()[0].lstrip('# ')
    (ROOT/(name+'.html')).write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+css+'</style><body>'+html+'</body></html>')

for name in ('report','experiment_details'):
    render(name, template=True)
for name in ('protocol_design','audit_review','baseline_protocol'):
    render(name)
print('Built separate report, experiments, protocol, audit and baseline documents')
