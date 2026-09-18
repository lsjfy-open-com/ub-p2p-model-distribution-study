# UB＋P2P 模型分发研究交付

优先阅读 `report.html`（离线可打开，图表已内嵌）或 `report.md`。这是自编的资源/调度级仿真，不是 UB/TCP 协议实现，不是实机 benchmark。

## 文件

- `protocol_design.html` / `protocol_design.md`：2026-09-18 新增的架构图、传输时序与协议草案（独立工程附录，未实现）。
- `protocol/model_distribution.proto`：自定义应用协议 schema；不等于 UB 底层协议，也不是运行中的服务。
- `protocol/transport_interface.py`：本地传输接口契约，TCP/URMA 后端尚未实现。
- `draw_protocol.py`：两张协议图的可编辑源；macOS 自动使用 PingFang，其他系统需配置中文字体。
- `protocol_validation.txt`：protobuf 编译和生成描述符检查结果，不代表硬件/状态机验证。

- `report.html` / `report.md`：研究报告、社区证据、规格与假设、计算、结果和工程方案。
- `simulator.py`：分块离散事件模拟器；所有大小使用 GB，所有带宽使用 **GB/s**。
- `run_experiments.py`：完整参数扫描与四张图。
- `test_simulator.py` / `validation.txt`：历史 12 项自动化测试及实际输出；新增检查见 audit_validation.txt。
- `results.csv` / `results.json`：每个场景的完整参数与结果。
- `environment.json` / `requirements-lock.txt`：实际执行环境和依赖版本。
- `baseline_protocol.md`：现有 TCP 和未来 UB 实机对照规程，尚未执行。
- `build_report.py` / `report_template.md`：用结果自动生成报告。
- `example_config.json`：单个场景参数示例。
- `figures/`：图表 PNG；`run*.log`：实际运行日志。
- `SHA256SUMS.txt`：交付文件摘要。

## 重现全部实验

需要 Python 3.9 或更新版本。推荐在独立环境执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v test_simulator.py
python run_experiments.py --workers 4
python build_report.py
```

可选的协议语法校验（生成物放在临时目录，不纳入源码）：

```bash
python -m pip install -r requirements-protocol.txt
mkdir -p build/protocol
python -m grpc_tools.protoc -I protocol --python_out=build/protocol --grpc_python_out=build/protocol protocol/model_distribution.proto
python draw_protocol.py
python build_report.py
```

`requirements-lock.txt` 保留原仿真实验依赖；协议工具版本见 `requirements-protocol.txt`。

完整重跑需要数分钟，主要耗时是 15.625 MB 分块的 100 节点场景。实际速度依赖本地 CPU；不会分配 14 TB 真实模型数据。内存中只保存块状态和事件。

`--resume` 已禁用：历史结果没有代码指纹，按 label 跳过会混入不同版本；修改后应完整重跑。`--plots-only` 只从现有 results.json 重画图。

## 单独修改场景

```bash
python simulator.py --config example_config.json --output custom_result.json
```

配置字段对应 `Config`。例子保留了有限全局容量与内存预算，更接近需要检查的受限场景，但仍非任何实机规格。

## 结果解释边界

1. N 是空客户端数，种子额外计数。多种子预热成本未计入分发时间。
2. fixed P2P 是分块流水线链，不是自适应最优 swarm；大窗口、慢节点、拥塞可使其变差。
3. `time_s` 是所有节点数据可用时间，不是推理服务 ready。
4. `source_gb` 是全部种子发送之和；原始权威仓库的磁盘 IO 与预热 IO 未模拟。
5. `peak_total_gbps` 是瞬时逻辑 payload 聚合值，不是逐跳线速峰值。
6. `1e9` 容量用作“不构成瓶颈”的哨兵，不代表硬件规格。
7. 代码不运行 URMA 或 TCP；带宽参数相同则传输名称不改变结果。
8. 结果小数用于复核，不表示真实机器有相应精度。
9. 实际运行的 Python/依赖版本可见 environment.json 和 requirements-lock.txt；不同浮点环境可能产生极小差异。

完整参数与历史结果在 experiment_details.md，审核结论在 audit_review.md。任何现场测试和硬件采购都需用实际拓扑、路径及版本校准。

## 审核与本地项目位置

项目交付目录：`outputs/ub_p2p_study/`；Git 仓库根目录为其上两级。研究工作分支为 `codex/ub-p2p-study`。

阅读顺序：report → audit_review → experiment_details → baseline_protocol → protocol_design。每份都有 Markdown 和 HTML；HTML 图片内嵌，文档间链接需要保留同目录文件。

历史 122 条记录对应 113 个不同完整配置。此次审核保留 results.json/csv 原始字节，仅重跑代表场景并另存审计输出。

```bash
python -m unittest -v test_simulator.py
python audit_results.py
python draw_protocol.py
python run_experiments.py --plots-only
python build_report.py
```

`audit_results.py` 生成 audit_metrics.json；测试输出见 audit_validation.txt。各 GB/s 字段保持历史命名以兼容原始数据。构建顺序需先生成图，再生成 HTML。

## 草图映射部署图

`figures/deployment_proposal.png` / `.svg`：保留容器 OM、Easysuit、Job、HOFS 与推理服务的部署提案；职责和待确认项见 `deployment_notes.md`。执行 `python draw_deployment.py` 可重新生成。
