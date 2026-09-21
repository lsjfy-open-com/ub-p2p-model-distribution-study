# UB + P2P 模型分发研究

研究 50～100 节点同时准备模型时，集中供数、多热种子与固定链式分块转发的资源瓶颈，并设计未来 UB / URMA 数据后端。

**当前成果是资源与调度仿真，不是 TCP、UB 或 Ascend 实机 benchmark。** 历史数据包含 122 条记录、113 个不同配置；协议与传输接口是待实现草案。

## 阅读入口

|内容|入口|
|---|---|
|UB 带宽/功耗、Mooncake 与 SSD 演进（2026-09-20）|[专题研究](outputs/ub_p2p_study/ub_capacity_memory_evolution.md)|
|UB 带宽—功耗资料补充（2026-09-21）|[证据与缺失数据](outputs/ub_p2p_study/ub_power_evidence.md)|
|完整研究报告|[report.md](outputs/ub_p2p_study/report.md)|
|架构部署图及草图映射|[deployment_notes.md](outputs/ub_p2p_study/deployment_notes.md)|
|PV / CSI / HOFS、FRP / SFTP 与 50 节点计算|[storage_bandwidth_faq.md](outputs/ub_p2p_study/storage_bandwidth_faq.md)|
|技术自审、修订及证据边界|[audit_review.md](outputs/ub_p2p_study/audit_review.md)|
|模型、参数与全部实验结果|[experiment_details.md](outputs/ub_p2p_study/experiment_details.md)|
|现有 TCP 与未来 UB 实机验证规程|[baseline_protocol.md](outputs/ub_p2p_study/baseline_protocol.md)|
|分层协议及接口草案|[protocol_design.md](outputs/ub_p2p_study/protocol_design.md)|
|详细复现说明|[实验目录 README](outputs/ub_p2p_study/README.md)|

![部署方案](outputs/ub_p2p_study/figures/deployment_proposal.png)

## 快速复现

从仓库根目录执行，Python 3.9 或更新版本：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r outputs/ub_p2p_study/requirements.txt
python -m unittest discover -s outputs/ub_p2p_study -p test_simulator.py -v
python outputs/ub_p2p_study/audit_results.py
```

完整重跑会覆盖结果文件，建议在新的工作分支执行：

```bash
python outputs/ub_p2p_study/run_experiments.py --workers 4
python outputs/ub_p2p_study/build_report.py
```

`--plots-only` 使用现有结果重画统计图；`--resume` 已禁用以避免混入不同版本结果。中文架构图脚本使用 macOS PingFang 字体；其他平台需提供可用中文字体，已提交的 PNG/SVG 可直接查看。HTML 报告需下载后本地打开，GitHub 文件页以 Markdown 为阅读入口。

## 数据与版本管理

- `results.json` / `results.csv`：历史参数与数值结果，单位 GB、GB/s、秒；历史字段 `*_gbps` 表示 GB/s。
- `audit_metrics.json` / `audit_validation.txt`：历史结果复核和代表场景重算记录。
- `environment.json` / `requirements-lock.txt`：原仿真环境记录，不等同于当前机器环境。
- `protocol/`：可编译应用 schema 和接口契约，不包含运行中的 RPC 服务或 TCP/URMA 后端。
- `SHA256SUMS.txt`：实验交付目录文件摘要；重新生成文件后需更新。

保留原本地研究提交历史及 `codex/ub-p2p-study` 工作分支。`main` 作为已整理的交付入口。虚拟环境、临时生成物和重复 ZIP 不提交；第三方社区资料以来源链接引用，不复制整站文档。
