# Skill 包索引

## 已通过候选

| Skill | 解决的问题 | 主要触发场景 | 关系 |
|---|---|---|---|
| `agentic-workflow-compounding` | 把一次性聊天迁移成能行动、留存和复用的 agent 工作流 | 反复复制上下文、手工搬运结果、想让 AI 真正完成任务 | 与 `context-capital-routing`、`operational-skill-audit` 组合 |
| `context-capital-routing` | 积累、提炼并按任务选择上下文 | 资料很多但每次仍从零解释，或全部材料一股脑塞给 AI | 支撑 `agentic-workflow-compounding` |
| `operational-skill-audit` | 判断一个 Skill 是否真正可执行 | 审查 Skill、怀疑它只是风格 prompt、准备发布前质检 | 可审计其他三个 Skill |
| `question-seed-generalism` | 用跨领域最低入口生成高质量问题与连接 | 进入陌生领域、设计广度学习、完全不知道该问什么 | 可与普通研究流程组合 |

## 推荐使用顺序

1. 对反复出现的真实任务，先用 `agentic-workflow-compounding` 重构载体。
2. 用 `context-capital-routing` 建立可复用的上下文资产与选择规则。
3. 需要固化流程时制作 Skill，再用 `operational-skill-audit` 做发布前审查。
4. 当任务卡在“陌生到不知道问什么”时，用 `question-seed-generalism` 建立入口。

## 测试状态

- 每个 Skill：7 个测试，包括 3 个应触发、2 个不应触发、1 个边界场景和 1 个执行验收。
- 本轮采用主流程自测，未使用独立盲测，因此触发可信度标记为“中等”。
- 结构、JSON、诱饵和总通过率的实际结果见 `VALIDATION_REPORT.md`。

## 安装状态

已于 2026-08-08 获得用户明确授权并安装到 `~/.codex/skills/`。安装后完成文件一致性、结构和触发抽查，结果通过；详见 `INSTALLATION_REPORT.md`。
