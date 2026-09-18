"""Render the architecture and read-based chunk protocol; no hardware execution."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parent
font_path=Path('/System/Library/Fonts/PingFang.ttc')
FONT=FontProperties(fname=str(font_path)) if font_path.exists() else FontProperties(family='sans-serif')
INK='#193647';TEAL='#008b78';BLUE='#377fbc';GRAY='#657987'
def text(ax,x,y,s,size=13,color=INK,ha='center',weight='normal'):
    ax.text(x,y,s,ha=ha,va='center',fontsize=size,color=color,fontproperties=FONT,weight=weight)
def box(ax,x,y,w,h,s,fill='#edf6f4',size=13):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=.12',
                              facecolor=fill,edgecolor='#b9cbc9',linewidth=1))
    text(ax,x+w/2,y+h/2,s,size)
def arrow(ax,x1,y1,x2,y2,label='',dashed=False,color=TEAL,dy=.2):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='->',lw=1.7,color=color,
                                                         linestyle='--' if dashed else '-'))
    if label:text(ax,(x1+x2)/2,(y1+y2)/2+dy,label,11,color)
def canvas(h):
    fig,ax=plt.subplots(figsize=(13,h));ax.set_xlim(0,13);ax.set_ylim(0,h);ax.axis('off')
    fig.subplots_adjust(left=.02,right=.98,top=.98,bottom=.02);return fig,ax

fig,ax=canvas(9.8)
text(ax,6.5,9.4,'UB＋P2P：调度模式与传输协议分层',21)
text(ax,6.5,8.95,'方案草案 v0.2｜控制面可用 TCP，模型数据可走原生 UB',12,GRAY)
box(ax,3.9,7.7,5.2,.8,'协调器：Manifest · 分块位置 · 拓扑 · 限流','#edf2fa',14)
for x in [1.7,5.5,9.8]:
    arrow(ax,6.5,7.7,x,6.65,dashed=True,color=BLUE)
text(ax,10.6,7.5,'虚线：控制 RPC\ngRPC＋TLS / TCP',11,BLUE)
box(ax,.3,5.25,2.8,1.4,'热种子\n权威模型的已校验副本\n块 0、1、2…',size=12)
box(ax,4.1,5.25,2.8,1.4,'Peer A：接收＋供数\n完成 → 校验 → 发布\n本地模型加载器',size=12)
box(ax,8.4,5.25,2.8,1.4,'Peer B / 后续节点\n完整块校验后可转发\n不等整个模型',size=12)
arrow(ax,3.1,5.9,4.1,5.9,'块 j',dy=.35)
arrow(ax,6.9,5.9,8.4,5.9,'块 j',dy=.35)
arrow(ax,11.2,5.9,12.6,5.9,'…',dy=.35)
text(ax,6.5,4.7,'实线：逻辑数据流；采用拉取时，由接收 Peer 发起 READ',12,TEAL)
box(ax,1,3.55,11, .65,'统一应用接口：fetch_chunk → poll → verify → publish；cancel_and_drain 后才释放',size=12)
arrow(ax,3.5,3.55,3.5,2.9)
arrow(ax,9.5,3.55,9.5,2.9)
box(ax,1,1.8,5,1.1,'TCP 后端：基线待实现\n长度分帧 / 流式接收 → 完整性校验','#f1f4f7',12)
box(ax,7,1.8,5,1.1,'UB 后端：未来实现\n内存注册 / 导入 → URMA READ → JFC','#edf6f4',12)
text(ax,6.5,1.3,'两种后端择一传块，使用相同 Manifest 和校验；禁止静默回退',12)
text(ax,6.5,.72,'不新增 UB 硬件协议；应用层约定分块、租约、幂等、发布与故障处理',12)
text(ax,6.5,.27,'本图为工程设计；历史 122 条记录（113 个配置）只模拟带宽、分块依赖和调度。',11,GRAY)
fig.savefig(ROOT/'figures/architecture.png',dpi=180);plt.close(fig)

fig,ax=canvas(12)
text(ax,6.5,11.6,'一个分块如何通过 UB 拉取并成为新的数据源',20)
text(ax,6.5,11.1,'v0.2 首选 READ｜本地完成、内容校验和服务就绪是不同事件',12,GRAY)
xs=[1.35,4.65,8,11.45]
for x,name in zip(xs,['协调器','源 Peer A','接收 Peer B','后续 Peer C']):
    box(ax,x-1.1,10.25,2.2,.55,name,size=12)
    ax.plot([x,x],[1.05,10.25],ls=':',lw=1,color='#a5b7c1')
def msg(i,j,y,s,data=False):arrow(ax,xs[i],y,xs[j],y,s,dashed=not data,color=TEAL if data else BLUE,dy=.2)
msg(2,0,9.65,'1  LocateChunk：模型摘要＋块 ID')
msg(0,2,8.95,'2  候选源＋源会话 epoch')
msg(2,1,8.25,'3  AcquireReadLease：协商后端、锁定块')
msg(1,2,7.55,'4  租约＋限额＋受保护的后端描述符')
msg(2,1,6.85,'5  READ 请求：匹配 SDK 的 URMA 操作',True)
msg(1,2,6.15,'6  数据：UB Fabric → 已注册本地缓冲',True)
box(ax,6.52,4.65,3,1,'7  B 等待所有操作成功完成\n核对长度、generation、哈希\n本地原子进入 VERIFIED',size=11)
msg(2,0,4.1,'8  ReportChunk：校验完成，允许定位 B')
msg(2,1,3.4,'9  停止提交并 drain 后，ReleaseReadLease')
msg(3,2,2.7,'10  C 获取 B 的独立租约')
msg(2,3,2,'11  B 为 C 提供同一已校验块',True)
text(ax,6.5,.6,'租约过期≠在途 DMA 已结束；超时必须取消、排空或隔离缓冲后才能复用。',12)
text(ax,6.5,.2,'步骤 8 与 9 可按依赖并行；源块在所有读取租约结束前必须保持不可变。',11,GRAY)
fig.savefig(ROOT/'figures/chunk_sequence.png',dpi=180);plt.close(fig)
print('Rendered architecture.png and chunk_sequence.png')

fig,ax=canvas(8.4)
text(ax,6.5,8.05,'同一份权威模型 ≠ 全系统只有一份数据',21)
text(ax,6.5,7.55,'本研究：启动前的分块分发；不模拟运行时跨节点共享权重',13,GRAY)
box(ax,.35,5.5,2.5,1.15,'热种子\n持有完整模型 S',size=14)
box(ax,4,5.5,2.4,1.15,'Peer A\n接收、校验、转发',size=13)
box(ax,7.4,5.5,2.4,1.15,'Peer B\n接收、校验、转发',size=13)
box(ax,10.7,5.5,1.95,1.15,'… Peer N\n本地缓存',size=13)
arrow(ax,2.85,6.1,4,6.1,'块 j',dy=.3)
arrow(ax,6.4,6.1,7.4,6.1,'块 j',dy=.3)
arrow(ax,9.8,6.1,10.7,6.1,'块 j',dy=.3)
text(ax,6.5,4.95,'固定链实验：源共发 S；Peer 共发 (N−1)S；最终客户端缓存共 NS',13,TEAL)
box(ax,.35,3.45,5.9,.95,'当前已执行：资源与调度模拟\n带宽预算、分块依赖、固定链；无网络协议',fill='#edf2fa',size=13)
box(ax,6.65,3.45,6,.95,'后续实机：同一分发逻辑切换后端\nTCP baseline → UB / URMA READ',size=13)

box(ax,.35,1.85,12.3,.95,'分发完成后：模型加载 → 权重进入 HBM → warmup → 服务 ready\n本次均未模拟；这些阶段必须在 Ascend 实机另行测量',fill='#f1f4f7',size=13)
text(ax,6.5,1.15,'前提：每个节点需要完整 S。若按 shard 部署，应按各节点实际缺块重新建模。',12)
text(ax,6.5,.6,'P2P 选择数据来源；UB 提供传输路径。共享 fabric 受限时，两者都无法突破容量上限。',12,GRAY)
fig.savefig(ROOT/'figures/overview.png',dpi=180);plt.close(fig)
