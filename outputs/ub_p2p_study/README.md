# UB＋P2P 模型分发研究交付

优先阅读 `report.html`（离线可打开，图表已内嵌）或 `report.md`。这是自编的资源/调度级仿真，不是 UB/TCP 协议实现，不是实机 benchmark。

## 文件

- `report.html` / `report.md`：研究报告、社区证据、规格与假设、计算、结果和工程方案。
- `simulator.py`：分块离散事件模拟器；所有大小使用 GB，所有带宽使用 **GB/s**。
- `run_experiments.py`：完整参数扫描与四张图。
- `test_simulator.py` / `validation.txt`：12 项自动化测试及实际输出。
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

完整重跑需要数分钟，主要耗时是 15.625 MB 分块的 100 节点场景。实际速度依赖本地 CPU；不会分配 14 TB 真实模型数据。内存中只保存块状态和事件。

`--resume` 按已完成结果的 label 跳过场景，只适用于同一代码/参数版本的补跑；修改模型或场景后必须完整重跑，不能用 resume 冒充新结果。`--plots-only` 从现有 results.json 重画图。

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

完整参数、引用与局限在报告正文。任何现场测试和硬件采购都需用实际拓扑、路径及版本校准。
