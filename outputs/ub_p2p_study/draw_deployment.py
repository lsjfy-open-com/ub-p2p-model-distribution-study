"""Deployment proposal based on the user's OM / business-plane sketch."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent
FONT=FontProperties(fname='/System/Library/Fonts/PingFang.ttc')
INK='#193647';BLUE='#357eb8';GREEN='#008976';ORANGE='#a46b26';GRAY='#657987'
fig,ax=plt.subplots(figsize=(16,12));ax.set(xlim=(0,16),ylim=(0,12));ax.axis('off')
fig.subplots_adjust(left=.015,right=.985,top=.985,bottom=.015)
def txt(x,y,s,size=13,color=INK,ha='center'):
 ax.text(x,y,s,ha=ha,va='center',fontsize=size,color=color,fontproperties=FONT)
def box(x,y,w,h,s='',fill='white',edge='#b8c9d2',size=13):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=.09',facecolor=fill,edgecolor=edge,lw=1.2))
 if s:txt(x+w/2,y+h/2,s,size)
def path(points,color=BLUE,dash=True,lw=1.5,both=False):
 xs,ys=zip(*points)
 ax.plot(xs[:-1],ys[:-1],color=color,lw=lw,ls='--' if dash else '-')
 ax.annotate('',xy=points[-1],xytext=points[-2],arrowprops=dict(arrowstyle='<->' if both else '->',color=color,lw=lw,linestyle='--' if dash else '-'))
txt(8,11.65,'UB＋P2P 模型分发：部署方案',23)
txt(8,11.23,'沿用草图的容器 OM 与业务面分层｜设计方案，尚未完成实机验证',12,GRAY)
box(.4,8.65,15.2,2.15,fill='#f1f5fa')
txt(.7,10.5,'容器 OM · 管理面',15,ha='left')
box(.9,9.08,3.1,.95,'Easysuit\n模型版本发布 / Job 编排',size=13)
box(4.8,9.08,4.5,.95,'模型制品目录\nhostPath 或共享存储 PV（需明确）',size=13)
box(10.1,9.08,4.95,.95,'P2P Service · 控制服务\nManifest / 块位置 / 选源 / 授权',size=13)
path([(4,9.55),(4.8,9.55)],GRAY)
txt(4.4,9.9,'发布',10,GRAY)
path([(9.3,9.55),(10.1,9.55)],BLUE)
txt(9.7,9.9,'登记',10,BLUE)
box(.4,1.5,15.2,6.7,fill='#fafcfd')
txt(1.25,7.95,'业务面 · 各节点按需缓存并提供已校验块',15,ha='left')
xs=[1.25,6.1,10.95]
for x,title in zip(xs,['节点 1 · 初始种子 / Peer','节点 2 · Peer','节点 N · Peer']):
 box(x,1.85,3.8,5.6,fill='white')
 txt(x+1.9,7.12,title,14)
 box(x+.3,6.25,3.2,.55,'Job：发起本节点模型准备',fill='#eef3fa',size=12)
 box(x+.3,4.98,3.2,.9,'P2P Agent（拟新增）\n传输 / 校验 / UB 注册缓冲',fill='#e8f6f1',size=12)
 box(x+.3,3.55,3.2,.9,'HOFS / 本地模型缓存\n已校验块可供其他 Peer 读取',fill='#edf7f3',size=12)
 box(x+.3,2.22,3.2,.75,'推理服务\n本地加载 → HBM → ready',fill='#fff5e8',size=12)
 path([(x+1.9,6.25),(x+1.9,5.88)],BLUE)
 path([(x+1.9,4.98),(x+1.9,4.45)],GREEN,False,both=True)
 txt(x+2.6,4.72,'供块 / 写缓存',10,GREEN)
 path([(x+1.9,3.55),(x+1.9,2.97)],ORANGE,False)
 txt(x+2.62,3.26,'加载所需 shard',10,ORANGE)
# P2P control bus routed to the agents without passing through jobs.
path([(14.9,9.08),(15.25,9.08),(15.25,6.02),(1.9,6.02),(1.9,5.88)],BLUE)
for x in xs[1:]:path([(x+.65,6.02),(x+.65,5.88)],BLUE)
txt(11,8.45,'蓝虚线：控制 RPC；P2P Service 不转发大块模型数据',11,BLUE)
# Initial injection routed outside the first node.
path([(5.1,9.08),(5.1,8.48),(.75,8.48),(.75,4),(1.55,4)],GREEN,False,lw=2)
txt(2.75,8.66,'① 制品可达路径 → 初始种子预热',11,GREEN)
# Native backend traffic between peer agents.
for left,right in zip(xs,xs[1:]):
 path([(left+3.5,5.4),(right+.3,5.4)],GREEN,False,lw=2.5)
 txt((left+3.5+right+.3)/2,5.73,'② 分块转发',10,GREEN)
 txt((left+3.5+right+.3)/2,5.06,'UB / URMA',10,GREEN)
txt(8,1.08,'绿实线：模型数据方向（采用 READ 时，请求方向相反）｜橙实线：本地加载',12)
txt(8,.67,'当前验证路径：TCP 后端；目标路径：UB 后端。链式为首版实验策略，后续可替换选源拓扑。',12,GRAY)
txt(8,.27,'“HOFS 缓存备份”按可选跨节点块副本处理；需另定副本数与持久化策略，不默认本机双份具备容灾能力。',11,GRAY)
for ext in ('png','svg'):
 fig.savefig(ROOT/f'figures/deployment_proposal.{ext}',dpi=180)
plt.close(fig)
