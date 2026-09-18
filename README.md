# UB＋P2P 模型分发研究

本地项目仓库，用于管理研究报告、仿真代码、实验参数与结果。

- `main`：项目管理基础。
- `codex/ub-p2p-study`：研究与实验工作分支，历史快照包含 122 条记录（113 个不同配置），审核版通过 13 项单元测试。
- 报告入口：[`outputs/ub_p2p_study/report.md`](outputs/ub_p2p_study/report.md)。
- 复现说明：[`outputs/ub_p2p_study/README.md`](outputs/ub_p2p_study/README.md)。
- 实机验证规程：[`outputs/ub_p2p_study/baseline_protocol.md`](outputs/ub_p2p_study/baseline_protocol.md)。
- 架构图与协议草案：[`outputs/ub_p2p_study/protocol_design.md`](outputs/ub_p2p_study/protocol_design.md)（2026-09-18 补充，接口通过语法校验，后端待实现）。

代码、参数、结果和报告纳入版本管理；本地虚拟环境、临时文件和重复打包的 ZIP 不纳入版本管理。当前结果为资源与调度仿真，不是 UB 或 Ascend 实机测试。

后续修改在工作分支提交，结果应与生成它的代码、配置一起提交。更新实验结果后重新生成报告及交付摘要，避免混用不同版本。

2026-09-18 技术自审：主报告重写为 v2；实验与协议拆成独立附录；详见 outputs/ub_p2p_study/audit_review.md。
